#!/home/kevin/.py-virtualenvs/ssh/bin/python
import paramiko
import os
from datetime import date

# might need to set ownership values correctly

class RotateKeys():
    def __init__(self, hostname, ssh_home="/home/kevin/.ssh"):
        self.hostname = hostname
        self.ssh_config = os.path.join(ssh_home, "config")
        self.signature = ".".join([self.hostname, date.today().strftime("%Y%m%d")])

        self.init_client()

        self.get_ssh_config()

        self.sshkeyfile = os.path.basename(self.config.get('identityfile')[0])

        self.generate()

        self.connect()

        self.command()

        self.disconnect()

        self.replace()

    
    def init_client(self):
        self.client = paramiko.client.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def get_ssh_config(self):
        '''
        get config for current host
        '''
        config = paramiko.config.SSHConfig()
        config.parse(open(self.ssh_config))
        self.config = config.lookup(self.hostname)
        return
            

    def generate(self):
        '''
        generate new ssh key pair
        '''
        self.sshkey = paramiko.RSAKey.generate(4096)

        self.public = f"{self.sshkey.get_name()} {self.sshkey.get_base64()} {self.signature}"
        
        self.sshkey.write_private_key_file(self.sshkeyfile)

        with open(f"{self.sshkeyfile}.pub", 'w') as f:
            f.write(self.public)
        
    def connect(self):
        self.client.connect(
            hostname=self.config.get('hostname'),
            username=self.config.get('user'),
            port=self.config.get('port', 22),
            key_filename=self.config.get('identityfile')
        )
        return

    def command(self):
        '''
        replace pubkey in authorized_keys on host
        '''
        # holy one-liner
        cmd = f"sed -i.backup '/ssh-rsa.*{self.hostname}.*/d' /home/{self.config['user']}/.ssh/authorized_keys ; echo {self.public} >> /home/{self.config['user']}/.ssh/authorized_keys"
        
        self.client.exec_command(cmd)
        return
    

    def disconnect(self):
        self.client.close()

    def replace(self):
        '''
        replace old keys with new keys
        '''
        # move old to old folder, just in case
        try:
            os.rename(f'/home/kevin/.ssh/{self.sshkeyfile}',f'/home/kevin/.ssh/old/{self.sshkeyfile}')
            os.rename(f'/home/kevin/.ssh/{self.sshkeyfile}.pub',f'/home/kevin/.ssh/old/{self.sshkeyfile}.pub')
        except FileNotFoundError:
            print("Previous file not found, maybe it was called something else?")

        os.rename(f'/home/kevin/projects/python/ssh/{self.sshkeyfile}',f'/home/kevin/.ssh/{self.sshkeyfile}')
        os.rename(f'/home/kevin/projects/python/ssh/{self.sshkeyfile}.pub',f'/home/kevin/.ssh/{self.sshkeyfile}.pub')

def main():
    hostnames = [
        # "caspian",
        # "oracle-minecraft",
        "vanessa",]
    for hostname in hostnames:
        RotateKeys(hostname)

    

if __name__ == "__main__":
    main()