"""
CoNLL-U processing: parsing, text extraction, annotation mapping
"""
import uuid
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class Token:
    """Represents a single CoNLL-U token"""
    def __init__(self, line: str):
        fields = line.split('\t')
        if len(fields) != 10:
            raise ValueError(f"Invalid CoNLL-U token line: {line}")
        
        self.id = fields[0]
        self.form = fields[1]
        self.lemma = fields[2]
        self.upos = fields[3]
        self.xpos = fields[4]
        self.feats = fields[5]
        self.head = fields[6]
        self.deprel = fields[7]
        self.deps = fields[8]
        self.misc = fields[9]
        
    def has_space_after(self) -> bool:
        """Check if token should be followed by space"""
        return 'SpaceAfter=No' not in self.misc
    
    def add_annotation(self, annotation: str):
        """Add annotation to MISC field"""
        if self.misc == '_':
            self.misc = annotation
        else:
            self.misc += '|' + annotation
    
    def to_conllu(self) -> str:
        """Serialize token back to CoNLL-U format"""
        return '\t'.join([
            self.id, self.form, self.lemma, self.upos, self.xpos,
            self.feats, self.head, self.deprel, self.deps, self.misc
        ])


class Sentence:
    """Represents a CoNLL-U sentence with comments and tokens"""
    def __init__(self):
        self.comments: List[str] = []
        self.tokens: List[Token] = []
        self.text: Optional[str] = None
        
    def get_text(self) -> str:
        """Extract or reconstruct sentence text"""
        # Try to get from "# text = ..." comment
        for comment in self.comments:
            if comment.startswith('# text = '):
                return comment[9:]
        
        # Reconstruct from tokens
        text = ''
        for token in self.tokens:
            if '-' not in token.id and '.' not in token.id:  # Skip multiword tokens
                text += token.form
                if token.has_space_after():
                    text += ' '
        return text.rstrip()
    
    def to_conllu(self) -> str:
        """Serialize sentence back to CoNLL-U format"""
        lines = self.comments + [token.to_conllu() for token in self.tokens]
        return '\n'.join(lines)


class CoNLLUProcessor:
    """Main processor for CoNLL-U operations"""
    
    SPEECH_ACTS = {
        '01_Situace': {'name': 'Situation', 'color': '#E8F5E9'},
        '02_Kontext': {'name': 'Context', 'color': '#E3F2FD'},
        '03_Postup': {'name': 'Procedure', 'color': '#FFF3E0'},
        '04_Proces': {'name': 'Process', 'color': '#F3E5F5'},
        '05_Podmínky': {'name': 'Conditions', 'color': '#FFFDE7'},
        '06_Doporučení': {'name': 'Recommendations', 'color': '#E0F2F1'},
        '07_Odkazy': {'name': 'Links', 'color': '#FCE4EC'},
        '08_Prameny': {'name': 'References', 'color': '#EFEBE9'},
        '09_Nezařaditelné': {'name': 'Not classified', 'color': '#ECEFF1'},
    }
    
    def parse_and_extract_text(self, conllu_text: str) -> Tuple[List[Sentence], str, List[Tuple]]:
        """
        Parse CoNLL-U and extract continuous text with token mapping
        
        Returns:
            sentences: List of Sentence objects
            text: Continuous text extracted from all sentences
            token_map: [(sent_idx, token_idx, char_start, char_end), ...]
        """
        sentences = []
        current_sentence = None
        
        for line in conllu_text.strip().split('\n'):
            line = line.rstrip()
            
            if not line:  # Empty line = sentence boundary
                if current_sentence and current_sentence.tokens:
                    sentences.append(current_sentence)
                current_sentence = None
                continue
            
            if line.startswith('#'):  # Comment
                if current_sentence is None:
                    current_sentence = Sentence()
                current_sentence.comments.append(line)
                continue
            
            # Token line
            if current_sentence is None:
                current_sentence = Sentence()
            
            # Skip multiword tokens and empty nodes
            token_id = line.split('\t')[0]
            if '-' in token_id or '.' in token_id:
                continue
                
            current_sentence.tokens.append(Token(line))
        
        # Add last sentence
        if current_sentence and current_sentence.tokens:
            sentences.append(current_sentence)
        
        # Build continuous text and token map
        text = ''
        token_map = []
        
        for sent_idx, sentence in enumerate(sentences):
            sent_text = sentence.get_text()
            sent_start = len(text)
            
            # Track each token's position
            char_pos = sent_start
            for tok_idx, token in enumerate(sentence.tokens):
                if '-' not in token.id and '.' not in token.id:
                    token_start = char_pos
                    token_end = char_pos + len(token.form)
                    token_map.append((sent_idx, tok_idx, token_start, token_end))
                    char_pos = token_end
                    if token.has_space_after():
                        char_pos += 1
            
            text += sent_text
            if sent_idx < len(sentences) - 1:
                text += ' '  # Space between sentences
        
        logger.info(f"Parsed {len(sentences)} sentences, extracted {len(text)} chars, {len(token_map)} tokens")
        return sentences, text, token_map
    
    def map_annotations_to_tokens(
        self, 
        sentences: List[Sentence], 
        annotations: List[Dict],
        token_map: List[Tuple]
    ) -> List[Sentence]:
        """
        Map character-based annotations to token MISC fields
        
        Args:
            sentences: Parsed sentences
            annotations: [{"start": int, "end": int, "label": str}, ...]
            token_map: [(sent_idx, token_idx, char_start, char_end), ...]
        """
        logger.info(f"Mapping {len(annotations)} annotations to {len(token_map)} tokens")
        for annotation in annotations:
            start_char = annotation['start']
            end_char = annotation['end']
            label = annotation['label']
            span_id = str(uuid.uuid4())[:8]
            
            logger.debug(f"Annotation: {label} chars {start_char}-{end_char}")
            
            # Find start and end tokens
            start_token = self._find_token_at_char(start_char, token_map)
            end_token = self._find_token_at_char(end_char - 1, token_map)  # end is exclusive
            
            logger.info(f"Annotation {label} ({start_char}-{end_char}): start_token={start_token}, end_token={end_token}")
            
            if start_token and end_token:
                sent_idx_start, tok_idx_start, _, _ = start_token
                sent_idx_end, tok_idx_end, _, _ = end_token
                
                # Add start annotation
                ann_start = f"PonkApp3:{label}:{span_id}=start"
                sentences[sent_idx_start].tokens[tok_idx_start].add_annotation(ann_start)
                
                # Add end annotation (if different token)
                if (sent_idx_start, tok_idx_start) != (sent_idx_end, tok_idx_end):
                    ann_end = f"PonkApp3:{label}:{span_id}=end"
                    sentences[sent_idx_end].tokens[tok_idx_end].add_annotation(ann_end)
                
                logger.debug(f"Mapped annotation {label} ({start_char}-{end_char}) to tokens")
        
        return sentences
    
    def _find_token_at_char(self, char_pos: int, token_map: List[Tuple]) -> Optional[Tuple]:
        """Find token that contains the given character position"""
        for token_info in token_map:
            sent_idx, tok_idx, start, end = token_info
            if start <= char_pos < end:
                return token_info
        return None
    
    def serialize_conllu(self, sentences: List[Sentence]) -> str:
        """Convert sentences back to CoNLL-U format"""
        return '\n\n'.join(sent.to_conllu() for sent in sentences) + '\n'
    
    def get_color_palette(self) -> Dict:
        """Return color palette for speech acts"""
        return {label: info['color'] for label, info in self.SPEECH_ACTS.items()}
