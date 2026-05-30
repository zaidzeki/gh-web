import re
import sys

def verify_xss():
    with open('app/static/js/app.js', 'r') as f:
        content = f.read()

    vulnerabilities = [
        {
            "name": "Production Ref Title XSS",
            "pattern": r'title="Production Ref: \${health\.production_status\.ref}"',
            "expected": r'title="Production Ref: \${escapeHTML\(health\.production_status\.ref\)}"'
        },
        {
            "name": "CI Status Title XSS",
            "pattern": r'title="CI Status: \${item\.ci_status}"',
            "expected": r'title="CI Status: \${escapeHTML\(item\.ci_status\)}"'
        },
        {
            "name": "Issue Label Color Style XSS",
            "pattern": r'style="background-color: #\${l\.color}',
            "expected": r'style="background-color: #\${escapeHTML\(l\.color\)}'
        }
    ]

    failed = False
    for v in vulnerabilities:
        matches = re.findall(v["pattern"], content)
        if matches:
            print(f"FAILED: Found vulnerability '{v['name']}' with pattern: {matches[0]}")
            failed = True
        else:
            # Check if it's already fixed
            if not re.search(v["expected"], content):
                # If neither pattern nor expected is found, maybe the code changed or we missed something
                # But for reproduction, we expect the pattern to be found.
                # Actually, during reproduction, we WANT to find the vulnerable pattern.
                pass
            else:
                print(f"PASSED: '{v['name']}' seems to be fixed or not present.")

    if failed:
        print("\nReproduction successful: Vulnerabilities found.")
        return 1
    else:
        print("\nNo vulnerabilities found.")
        return 0

if __name__ == "__main__":
    sys.exit(verify_xss())
