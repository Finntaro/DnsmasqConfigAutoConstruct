import argparse
import os
import logging
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
import yaml

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path):
    """加载并验证配置文件"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 验证必要配置项
    required = ['routers', 'file_mappings']
    for key in required:
        if key not in config:
            raise ValueError(f"Missing required config section: {key}")
    
    return config

def create_ssh_connection(router_config):
    """创建SSH连接"""
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    
    host = router_config['host']
    port = router_config.get('port', 22)
    username = router_config.get('username', 'admin')
    
    try:
        if 'password' in router_config:
            ssh.connect(
                hostname=host,
                port=port,
                username=username,
                password=router_config['password'],
                allow_agent=False,  # 新增：禁用SSH代理
                look_for_keys=False  # 新增：禁止查找本地密钥
            )
        elif 'key_file' in router_config:
            key_path = os.path.expanduser(router_config['key_file'])
            ssh.connect(
                hostname=host,
                port=port,
                username=username,
                key_filename=key_path
            )
        else:
            raise ValueError("Authentication method not specified")
        return ssh
    except Exception as e:
        logger.error(f"Connection to {host} failed: {str(e)}")
        return None

def ensure_remote_path_exists(ssh, remote_path):
    """确保远程路径存在"""
    dir_path = os.path.dirname(remote_path.rstrip('/'))
    if dir_path == '':  # 处理根目录情况
        return
    
    stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {dir_path}')
    if stdout.channel.recv_exit_status() != 0:
        error = stderr.read().decode()
        raise RuntimeError(f"Failed to create directory {dir_path}: {error}")

def upload_files(ssh, scp, file_mappings):
    """执行文件上传操作"""
    for mapping in file_mappings:
        local_path = mapping['local_path']
        remote_paths = mapping['remote_paths']
        
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            continue
            
        for remote_path in remote_paths:
            try:
                # 处理远程路径格式
                if remote_path.endswith('/'):
                    filename = os.path.basename(local_path)
                    full_remote = os.path.join(remote_path, filename).replace('\\', '/')
                else:
                    full_remote = remote_path
                
                ensure_remote_path_exists(ssh, full_remote)
                scp.put(local_path, full_remote)
                logger.info(f"Successfully uploaded {local_path} to {full_remote}")
            except Exception as e:
                logger.error(f"Failed to upload {local_path} to {remote_path}: {str(e)}")

def main(config_path='config.yaml'):
    """主函数"""
    config = load_config(config_path)
    
    for router in config['routers']:
        logger.info(f"Connecting to {router['host']}...")
        ssh = create_ssh_connection(router)
        if not ssh:
            continue
            
        try:
            transport = ssh.get_transport()
            if transport is None:
                raise RuntimeError("SSH transport is not available")            
            with SCPClient(transport) as scp:
                upload_files(ssh, scp, config['file_mappings'])
        except Exception as e:
            logger.error(f"SCP operation failed: {str(e)}")
        finally:
            ssh.close()
            logger.info(f"Disconnected from {router['host']}\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SCP文件上传工具')
    parser.add_argument('-c', '--config', required=False, default='config.yaml', help='配置文件路径')
    args = parser.parse_args()
    
    try:
        main(args.config)
    except Exception as e:
        logger.error(f"程序执行失败: {str(e)}")