import os
import re
import requests
import yaml

# 文件下载链接和名称
files = {
    "anti-ad.conf": "https://anti-ad.net/anti-ad-for-dnsmasq.conf",
    "Private_DIRECT.yaml": "https://raw.githubusercontent.com/Finntaro/PrivateClashRule/main/Private_DIRECT.yaml",
    "WeChat.yaml": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/WeChat/WeChat.yaml",
    "Oracle.yaml": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Oracle/Oracle.yaml",
    "Epic.yaml": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Epic/Epic.yaml",
    "SteamCN.yaml": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/SteamCN/SteamCN.yaml",
    "Bing.yaml": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Bing/Bing.yaml",
    "Microsoft.yaml": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Microsoft/Microsoft.yaml",
    "icloud.txt": "https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/icloud.txt",
    "apple.txt": "https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/apple.txt",
    "private.txt": "https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/private.txt",
    "direct.txt": "https://raw.githubusercontent.com/Loyalsoldier/clash-rules/release/direct.txt"
}

# 下载文件
def download_files():
    for filename, url in files.items():
        response = requests.get(url)
        with open(filename, 'w', encoding="utf-8") as file:
            file.write(response.text)
        print(f"{filename} 已下载")

# 从YAML文件和txt文件中提取域名
def extract_domains():
    domain_list = set()
    
    # 提取YAML文件中的域名
    yaml_files = ["Private_DIRECT.yaml", "WeChat.yaml", "Oracle.yaml", "Epic.yaml", "SteamCN.yaml", "Bing.yaml", "Microsoft.yaml"]
    for yaml_file in yaml_files:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            payload = data.get("payload", [])
            for entry in payload:
                if isinstance(entry, str):
                    if entry.startswith("DOMAIN,") or entry.startswith("DOMAIN-SUFFIX,"):
                        domain = entry.split(",")[1]
                        domain_list.add(domain)
                    elif entry.startswith("+."):
                        domain = entry[2:]
                        domain_list.add(domain)
    
    # 提取txt文件中的域名
    txt_files = ["icloud.txt", "apple.txt", "private.txt"]
    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    # 使用正则表达式提取域名
                    match = re.search(r"-\s*['\"]?(\+\.)?([a-zA-Z0-9.-]+)['\"]?", line)
                    if match:
                        domain = match.group(2)
                        domain_list.add(domain)

    return domain_list

# 从direct.txt文件中过滤域名
def filter_domains(domain_list):
    with open("direct.txt", 'r', encoding='utf-8') as f:
        direct_domains = {line.strip() for line in f if line.strip() and not line.startswith("#")}
    return domain_list - direct_domains

# 构建clash-core-bypass.conf配置文件
def build_bypass_config(filtered_domains):
    with open("clash-core-bypass.conf", "w", encoding="utf-8") as f:
        for domain in filtered_domains:
            f.write(f"nftset=/{domain}/4#inet#fw4#china_ip_route\n")
    print("clash-core-bypass.conf 已创建")

# 构建合并配置文件
def merge_configs():
    with open("anti-ad.conf", "r", encoding="utf-8") as ad_file:
        ad_content = ad_file.read()
    with open("clash-core-bypass.conf", "r", encoding="utf-8") as bypass_file:
        bypass_content = bypass_file.read()

    with open("anti-ad-bypass.conf", "w", encoding="utf-8") as merged_file:
        merged_file.write(ad_content + "\n" + bypass_content)
    print("anti-ad-bypass.conf 已创建")

# 主函数
def main():
    download_files()
    domains = extract_domains()
    filtered_domains = filter_domains(domains)
    build_bypass_config(filtered_domains)
    merge_configs()

if __name__ == "__main__":
    main()