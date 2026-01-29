# Deployment Guide - ponk-app3 VM

## Step 1: Copy files to the VM

From your local machine:

```bash
# Create tarball
cd ~/ufal/PONK-distilled_rules
tar czf ponk-app3.tar.gz ponk-app3/

# Copy to ufallab (jump host)
scp ponk-app3.tar.gz tpolak@ufallab.ms.mff.cuni.cz:/tmp/

# SSH to ufallab
ssh tpolak@ufallab.ms.mff.cuni.cz
```

From ufallab, copy to ponk-app3:

```bash
# Copy to ponk-app3
scp /tmp/ponk-app3.tar.gz tpolak@ponk-app3:/tmp/

# SSH to ponk-app3
ssh ponk-app3
```

## Step 2: Extract and setup on ponk-app3

```bash
# Extract
cd ~
tar xzf /tmp/ponk-app3.tar.gz
cd ponk-app3

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Create venv and install dependencies
uv venv
uv pip install flask requests
```

## Step 3: Test the service

```bash
# Run the app (foreground for testing)
.venv/bin/python app.py

# In another terminal/SSH session, test it:
curl http://localhost:8000/api/health
```

Expected output:
```json
{"service": "ponk-app3", "status": "ok"}
```

## Step 4: Run as background service

### Option A: Simple background process (for testing)

```bash
# Run in background with nohup
nohup .venv/bin/python app.py > app.log 2>&1 &

# Check it's running
curl http://localhost:8000/api/health

# View logs
tail -f app.log

# To stop: find process and kill
ps aux | grep app.py
kill <PID>
```

### Option B: systemd service (production-ready)

Create service file:

```bash
sudo nano /etc/systemd/system/ponk-app3.service
```

Paste this content (adjust paths if needed):

```ini
[Unit]
Description=PONK Module 3 - Speech Acts Annotation Service
After=network.target

[Service]
Type=simple
User=tpolak
WorkingDirectory=/home/tpolak/ponk-app3
ExecStart=/home/tpolak/ponk-app3/.venv/bin/python /home/tpolak/ponk-app3/app.py
Restart=always
RestartSec=10
StandardOutput=append:/home/tpolak/ponk-app3/app.log
StandardError=append:/home/tpolak/ponk-app3/app.log

# Environment variables (add when you have real LLM endpoint)
# Environment="UFAL_LLM_ENDPOINT=http://llm-server:8080/v1/chat/completions"
# Environment="UFAL_LLM_API_KEY=your_key"

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable ponk-app3

# Start the service
sudo systemctl start ponk-app3

# Check status
sudo systemctl status ponk-app3

# View logs
sudo journalctl -u ponk-app3 -f

# Restart if needed
sudo systemctl restart ponk-app3
```

## Step 5: Verify via quest proxy

From your local machine, test the public URL:

```bash
curl https://quest.ms.mff.cuni.cz/ponk-app3/api/health
```

Or open in browser:
```
https://quest.ms.mff.cuni.cz/ponk-app3/
```

## Step 6: Test annotation endpoint

Create a test file `test_request.json`:

```json
{
  "result": "# sent_id = 1\n# text = Nejvyšší správní soud rozhodl.\n1\tNejvyšší\tvysoký\tADJ\tAAIS1----3A----\tAnimacy=Inan|Case=Nom|Degree=Sup|Gender=Masc|Number=Sing|Polarity=Pos\t3\tamod\t_\t_\n2\tsprávní\tsprávní\tADJ\tAAIS1----1A----\tAnimacy=Inan|Case=Nom|Degree=Pos|Gender=Masc|Number=Sing|Polarity=Pos\t3\tamod\t_\t_\n3\tsoud\tsoud\tNOUN\tNNIS1-----A----\tAnimacy=Inan|Case=Nom|Gender=Masc|Number=Sing|Polarity=Pos\t4\tnsubj\t_\t_\n4\trozhodl\trozhodnout\tVERB\tVpYS----R-AAP-1\tAspect=Perf|Gender=Masc|Number=Sing|Polarity=Pos|Tense=Past|VerbForm=Part|Voice=Act\t0\troot\t_\tSpaceAfter=No\n5\t.\t.\tPUNCT\tZ:-------------\t_\t4\tpunct\t_\t_\n"
}
```

Test it:

```bash
curl -X POST https://quest.ms.mff.cuni.cz/ponk-app3/api/annotate \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

## Troubleshooting

### Service not accessible via quest proxy

Check if port 8000 is listening:
```bash
sudo netstat -tulpn | grep 8000
```

### Check quest proxy configuration

The quest proxy should already be configured by IT. If issues persist, contact IT to verify:
- Proxy from `https://quest.ms.mff.cuni.cz/ponk-app3/` → `http://10.10.51.187:8000/`

### View application logs

```bash
# If using systemd:
sudo journalctl -u ponk-app3 -f

# If using nohup:
tail -f ~/ponk-app3/app.log
```

### Restart the service

```bash
# systemd:
sudo systemctl restart ponk-app3

# nohup: kill and restart
pkill -f "python.*app.py"
cd ~/ponk-app3
nohup .venv/bin/python app.py > app.log 2>&1 &
```

## Next Steps for Production

1. **LLM Integration**: Update `llm_client.py` with actual UFAL LLM endpoint
2. **Configuration**: Set environment variables for API keys
3. **Monitoring**: Add proper logging and monitoring
4. **Error Handling**: Test with malformed CoNLL-U inputs
5. **Performance**: Test with large documents
6. **Coordination with JM**: 
   - Verify CoNLL-U format matches PONK expectations
   - Test integration with PONK frontend
   - Confirm color palette works in UI
