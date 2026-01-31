
import os
import sys
import datetime

# Configuration
JOURNAL_DIR = "/Users/rinne/Documents/Deka Scraping/Journal"

def get_journal_path():
    """
    Returns the absolute path for today's journal file (YYYY-MM-DD.md).
    Creates the Journal directory if it doesn't exist.
    """
    if not os.path.exists(JOURNAL_DIR):
        os.makedirs(JOURNAL_DIR)
        
    today = datetime.date.today().strftime("%Y-%m-%d")
    return os.path.join(JOURNAL_DIR, f"{today}.md")

def append_to_journal(title, content):
    """
    Safely appends a new entry to the daily Agent Journal.
    """
    journal_path = get_journal_path()
    
    # Check if file exists to determine if we need a header
    is_new_file = not os.path.exists(journal_path)
    
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    
    entry = ""
    if is_new_file:
        # Create file with Today's Header
        today_nice = datetime.date.today().strftime("%d %B %Y")
        entry += f"# Journal Entry: {today_nice}\n\n"
        
    entry += f"### {title} ({timestamp})\n"
    entry += content.strip() + "\n\n"
    
    try:
        with open(journal_path, "a", encoding="utf-8") as f:
            f.write(entry)
            
        print(f"✅ Successfully appended to journal: {os.path.basename(journal_path)}")
        return True
    except Exception as e:
        print(f"❌ Error updating journal: {e}")
        return False

if __name__ == "__main__":
    # Usage: python update_journal.py "Title" "Content"
    if len(sys.argv) < 3:
        print("Usage: python update_journal.py <Title> <Content>")
        sys.exit(1)
        
    title = sys.argv[1]
    content = sys.argv[2]
    
    append_to_journal(title, content)
