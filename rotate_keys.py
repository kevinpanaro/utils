#!/home/kevin/.py-virtualenvs/ssh/bin/python
import paramiko
from os import rename, path, chmod
import tempfile
from datetime import date

# might need to set ownership values correctly
# also this script is D A N G E R O U S
# used incorrectly and you'll be locked out
# probably because of some major oversight i failed to address
# use at own risk.

class RotateKeys():
    def __init__(self, hostname, ssh_home="/home/kevin/.ssh"):
        self.hostname = hostname
        self.ssh_home = ssh_home
        self.tmpdir = tempfile.TemporaryDirectory()

        self.get_ssh_config()

        self.set_paths()

        self.generate()

        self.connect()

        self.command()

        self.disconnect()

        self.replace()

        self.set_permissions()

        self.cleanup()


    def get_ssh_config(self):
        '''
        get config from host for current remote/client 
        '''
        ssh_config = path.join(self.ssh_home, "config")
        config = paramiko.config.SSHConfig()
        config.parse(open(ssh_config))
        self.config = config.lookup(self.hostname)
        return

    def set_paths(self):
        '''
        creates all the necessary paths we'll be using
        '''
        sshkeyfile = path.basename(self.config.get('identityfile')[0])
        self.paths = {
            "home_priv": path.join(self.ssh_home, sshkeyfile),
            "home_pub" : path.join(self.ssh_home, f'{sshkeyfile}.pub'),
            "old_priv" : path.join(self.ssh_home, "old", sshkeyfile),
            "old_pub"  : path.join(self.ssh_home, "old", f'{sshkeyfile}.pub'),
            "tmp_priv" : path.join(self.tmpdir.name, sshkeyfile),
            "tmp_pub"  : path.join(self.tmpdir.name, f'{sshkeyfile}.pub'),
        }

    def generate(self):
        '''
        generate new ssh key pair
        '''
        signature = ".".join([self.hostname, date.today().strftime("%Y%m%d")])

        sshkey = paramiko.RSAKey.generate(4096)

        self.public = f"{sshkey.get_name()} {sshkey.get_base64()} {signature}"
        
        sshkey.write_private_key_file(self.paths.get('tmp_priv'))

        with open(self.paths.get('tmp_pub'), 'w') as f:
            f.write(self.public)
    
    def init_client(self):
        self.client = paramiko.client.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        self.init_client()
        self.client.connect(
            hostname=self.config.get('hostname'),
            username=self.config.get('user'),
            port=self.config.get('port', 22),
            key_filename=self.config.get('identityfile')
        )
        return

    def command(self):
        '''
        replace pubkey in authorized_keys on remote/client
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
            rename(self.paths.get('home_priv'), self.paths.get('old_priv'))
            rename(self.paths.get('home_pub'), self.paths.get('old_pub'))
        except FileNotFoundError:
            # you're in danger if you see this because the script has already
            # changed the authorized_keys files. yikes.
            print("Previous file not found, maybe it was called something else?")

        rename(self.paths.get('tmp_priv'), self.paths.get('home_priv'))
        rename(self.paths.get('tmp_pub'), self.paths.get('home_pub'))

    def set_permissions(self):
        chmod(self.paths.get('home_priv'), 0o600)
        chmod(self.paths.get('home_pub'), 0o600)

    def cleanup(self):
        self.tmpdir.cleanup()

def main():
    hostnames = [
        "caspian",
        "oracle-minecraft",
        "vanessa",
        ]
    for hostname in hostnames:
        RotateKeys(hostname)

    

if __name__ == "__main__":
    main()