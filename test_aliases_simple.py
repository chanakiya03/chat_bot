
import sys
import os

# Add paths
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Minimal mock for loader
class MockLoader:
    def get_all_colleges(self):
        return [
            {'name': "Women's Christian College (WCC)", 'key': 'womens-christian-college'}
        ]

# Inject mock
import chatbot.engine.loader as loader
loader.get_all_colleges = MagicMock = lambda: [{'name': "Women's Christian College (WCC)", 'key': 'womens-christian-college'}]

from chatbot.engine.router import extract_colleges_fuzzy, ALIASES

def test_aliases():
    print("--- Testing ALIASES Mapping ---")
    print(f"Current ALIASES: {ALIASES}")
    
    assert ALIASES['wcc'] == 'womens-christian-college'
    
    # Test function
    keys = extract_colleges_fuzzy(["WCC"])
    print(f"Extracted keys for 'WCC': {keys}")
    assert 'womens-christian-college' in keys
    
    keys_lower = extract_colleges_fuzzy(["wcc"])
    print(f"Extracted keys for 'wcc': {keys_lower}")
    assert 'womens-christian-college' in keys_lower
    
    print("Alias mapping verified successfully!")

if __name__ == "__main__":
    test_aliases()
