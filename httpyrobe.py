import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import time

# Function to check if a domain is alive via HTTP
def check_http(domain, headers=None, timeout=5):
    http_url = f"http://{domain}"
    try:
        response = requests.get(http_url, headers=headers, timeout=timeout)
        if response.ok:  # Any 2xx or 3xx response is considered "alive"
            return http_url
    except requests.exceptions.RequestException:
        pass
    return None

# Function to check if a domain is alive via HTTPS
def check_https(domain, headers=None, timeout=5):
    https_url = f"https://{domain}"
    try:
        response = requests.get(https_url, headers=headers, timeout=timeout)
        if response.ok:  # Any 2xx or 3xx response is considered "alive"
            return https_url
    except requests.exceptions.RequestException:
        pass
    return None

# Function to check a domain with both HTTP and HTTPS protocols
def check_domain(domain, headers=None, timeout=5):
    # First, try HTTP
    result = check_http(domain, headers, timeout)
    if result:
        return result
    
    # If HTTP fails, try HTTPS
    result = check_https(domain, headers, timeout)
    if result:
        return result
    
    return None  # Return None if both checks fail

# Function to process domains concurrently with single-line status updates
def process_domains_concurrently(domains, headers=None, timeout=5, max_workers=10):
    alive_domains = []
    completed = 0
    total = len(domains)

    # Use ThreadPoolExecutor for concurrent domain processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_domain = {executor.submit(check_domain, domain, headers, timeout): domain for domain in domains}

        # Collect results as they complete
        for future in as_completed(future_to_domain):
            result = future.result()
            if result:
                alive_domains.append(result)
            completed += 1
            print(f"\r{completed}/{total} done", end="")  # Print the status on the same line

    print()  # Move to the next line after completion
    return alive_domains

if __name__ == "__main__":
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Efficient domain checker script with concurrency, custom headers, and real-time progress updates.")
    parser.add_argument("-f", "--file", help="Path to the file containing domains", required=True)
    parser.add_argument("-o", "--output", help="Path to save the output file (default: alive_domains.txt)", default="alive_domains.txt")
    parser.add_argument("-t", "--timeout", type=int, default=5, help="Request timeout in seconds (default: 5)")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Number of concurrent threads (default: 10)")
    parser.add_argument("-H", "--header", action="append", help="Custom headers in 'Header: Value' format. Can be used multiple times for multiple headers.")

    args = parser.parse_args()

    # Read domains from the specified file
    with open(args.file, "r") as file:
        domains = [line.strip() for line in file if line.strip()]
    
    # Initialize custom headers with a default User-Agent
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    # Add any additional headers specified by the user
    if args.header:
        for header in args.header:
            key, value = header.split(":", 1)
            custom_headers[key.strip()] = value.strip()

    start_time = time.time()
    
    # Process domains concurrently and get the list of alive domains
    alive_domains = process_domains_concurrently(domains, custom_headers, args.timeout, args.concurrency)
    
    # Write the alive domains with their protocol to the specified output file
    with open(args.output, "w") as alive_file:
        alive_file.write("\n".join(alive_domains))
    
    end_time = time.time()
    print("")
    print(f"Checked {len(domains)} domains in {end_time - start_time:.2f} seconds.")
    print(f"{len(alive_domains)} domains are alive.")
    print(f"Results saved to {args.output}.")
