from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pickle
import os.path
import csv

username = input("Enter a Twitter username which you want to scrape: ")

def check_csv_exist():
    global mode 
    if os.path.isfile(f"{username}_followers.csv"):
        mode= 'a'  # Append mode
    else:
        mode = 'w'  # Write mode

# Initialize webdriver and open Twitter login page
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://twitter.com/")

# Check if cookies file exists
def check_cookies():
    if os.path.exists("cookies_1.pkl"):
        # Load the cookies from the file
        with open("cookies_1.pkl", "rb") as f:
            cookies = pickle.load(f)

        # Add the cookies to the webdriver
        for cookie in cookies:
            driver.add_cookie(cookie)

        # Refresh the page to apply the cookies
        driver.get("https://twitter.com/"+ username)
    else:
        driver.get("https://twitter.com/login")
        input("Please authenticate and press Enter to continue...")
        cookies = driver.get_cookies()

        # Save the cookies to a file
        with open("cookies_1.pkl", "wb") as f:
            pickle.dump(cookies, f)
    
        check_cookies()


check_cookies()
check_csv_exist()
# Wait for the page to load
time.sleep(1)

# Click on the "People" tab
people_tab = driver.find_element("xpath",'//a[@href="/'+username+'/followers"]')
people_tab.click()

# Wait for the page to load
driver.implicitly_wait(10) # Wait up to 10 seconds for elements to appear

# Get existing followers from file and create a set
existing_followers = set()
if mode == 'a':
    with open(f'{username}_followers.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader) # Skip header row
        for row in reader:
            existing_followers.add((row[0], row[1], row[2]))

# Scrape new followers
followers = set()
print("scrapping...")
scroll_count = 0

while True:
    # scrape the data on the current page
    followersNames = driver.find_elements("xpath","//div[@data-testid='cellInnerDiv']//a[@class='css-4rbku5 css-18t94o4 css-1dbjc4n r-1loqt21 r-1wbh5a2 r-dnmrzs r-1ny4l3l' and not(contains(@tabIndex,'-1'))]")
    usernames = driver.find_elements("xpath","//div[@data-testid='cellInnerDiv']//a[@class='css-4rbku5 css-18t94o4 css-1dbjc4n r-1loqt21 r-1wbh5a2 r-dnmrzs r-1ny4l3l' and @tabIndex='-1']")
    for u, fn in zip(usernames, followersNames):
        if u.get_attribute("href") == fn.get_attribute("href"):
            follower = (u.text, fn.text, u.get_attribute("href"))
            if follower not in existing_followers:
                followers.add(follower)
    if (scroll_count + 1) % 10 == 0:
        check_csv_exist();
        with open(f'{username}_followers.csv', mode, newline='') as csvfile:
            writer = csv.writer(csvfile)
            if mode == 'w':
                writer.writerow(['Username', 'Name', 'Link'])
            for follower in followers:
                writer.writerow(follower)
        print(f"*{username}* Total uniques followers added in the csv = {len(followers)}")
        print("Taking a break for 5 minutes...")
        time.sleep(300) # wait for 5 minutes
        existing_followers.update(followers)
        followers.clear()
        print("Break finished.!")

    # scroll down to the next page
    last_height = driver.execute_script("return document.body.scrollHeight")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    new_height = driver.execute_script("return document.body.scrollHeight")

    scroll_count += 1

    # check if the scrollable height is the same as the previous height
    if new_height == last_height:
        break

with open(f'{username}_followers.csv', mode, newline='') as csvfile:
    print("Saving...")
    writer = csv.writer(csvfile)
    if mode == 'w':
        writer.writerow(['Username', 'Name', 'Link'])
    for follower in followers:
        writer.writerow(follower)

print(f"*{username}* Total followers scrapped = {len(existing_followers)}")

# Close the webdriver
driver.quit()