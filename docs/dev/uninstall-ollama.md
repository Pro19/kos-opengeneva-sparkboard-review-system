# Uninstall Ollama

Delete the Ollama binary:
Use the rm command to remove the Ollama binary. For example:
```bash
sudo rm /usr/local/bin/ollama
```

If the script created a systemd service, disable and remove it:
If the script created a systemd service for Ollama, you should disable and
remove it using the following commands:
```bash
sudo systemctl stop ollama
sudo systemctl disable ollama
sudo rm /etc/systemd/system/ollama.service
sudo systemctl daemon-reload
```

Remove any created user and group (if applicable):

The ollama installation script might have created a user and group named "ollama."
You can remove them using the following commands:
```bash
sudo userdel ollama
sudo groupdel ollama
```