import subprocess


class FirewallManager:
    def block_internet(self, file_path):
        command = f"netsh advfirewall firewall add rule name=\"Block\" dir=out program=\"{file_path}\" action=block"
        subprocess.run(command, shell=True)

    def unblock_internet(self, file_path):
        command = f"netsh advfirewall firewall delete rule name=\"Block\" program=\"{file_path}\""
        subprocess.run(command, shell=True)
