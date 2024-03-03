import asyncio
from aiogram import Bot, types, Dispatcher, executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from Keep_alive from Keep_alive
Keep_alive()

# Create an event loop
loop = asyncio.get_event_loop()

# Initialize the bot and dispatcher
bot = Bot(token="6558707003:AAGDYxc72mMrRBv71-ZsTkn2HqCCbq6sAZA")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Global variable for Selenium WebDriver
driver = None

class UserState(StatesGroup):
    waiting_for_credentials = State()
    waiting_for_password = State()

async def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('window-size=1200x600')

    return webdriver.Chrome(options=chrome_options)

async def login(driver, username, password):
    driver.get("https://mlritmexams.com/BeesERP/Login.aspx")

    username_input = await loop.run_in_executor(None, lambda: WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "txtUserName"))
    ))
    await loop.run_in_executor(None, lambda: username_input.send_keys(username))

    next_button = await loop.run_in_executor(None, lambda: driver.find_element(By.ID, "btnNext"))
    await loop.run_in_executor(None, lambda: driver.execute_script("arguments[0].click();", next_button))

    password_input = await loop.run_in_executor(None, lambda: WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "txtPassword"))
    ))
    await loop.run_in_executor(None, lambda: password_input.send_keys(password))

    submit_button = await loop.run_in_executor(None, lambda: driver.find_element(By.ID, "btnSubmit"))
    await loop.run_in_executor(None, lambda: driver.execute_script("arguments[0].click();", submit_button))

async def click_element_by_id(driver, element_id):
    element = await loop.run_in_executor(None, lambda: WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, element_id))
    ))
    await loop.run_in_executor(None, lambda: driver.execute_script("arguments[0].click();", element))

async def scrape_cgpa(driver):
    await click_element_by_id(driver, "ctl00_cpStud_lnkOverallMarksSemwiseMarks")

    cgpa = await loop.run_in_executor(None, lambda: WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ctl00_cpStud_lblMarks"))
    ))
    cgpa_score = cgpa.text.strip()

    return cgpa_score

async def scrape_attendance(driver):
    await click_element_by_id(driver, "ctl00_cpStud_lnkStudentMain")

    attendance_element = await loop.run_in_executor(None, lambda: WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ctl00_cpStud_lblTotalPercentage"))
    ))
    attendance_percentage = attendance_element.text.strip()

    return attendance_percentage

async def scrape_cgpa_percentage(driver):
    await click_element_by_id(driver, "ctl00_cpStud_lnkOverallMarksSemwiseMarks")

    cgpa_percentage_element = await loop.run_in_executor(None, lambda: WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "ctl00_cpStud_lblMarks"))
    ))
    cgpa_percentage = cgpa_percentage_element.text.strip()

    return cgpa_percentage*10

def is_dashboard_page(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_cpStud_lnkStudentMain"))
        )
        return True
    except:
        return False

async def start(message: types.Message):
    await message.answer("Hello! I'm here to help.")
    await message.answer("/cgpa - Get your CGPA.")
    await message.answer("/attendance - Get your attendance.")
    await message.answer("/cgpa_percentage - Get your CGPA percentage.")

async def cgpa(message: types.Message, state: FSMContext):
    await message.answer("Please enter your username:")
    await UserState.waiting_for_credentials.set()
    await state.update_data(command='cgpa')

async def attendance(message: types.Message, state: FSMContext):
    await message.answer("Please enter your username:")
    await UserState.waiting_for_credentials.set()
    await state.update_data(command='attendance')

async def cgpa_percentage(message: types.Message, state: FSMContext):
    await message.answer("Please enter your username:")
    await UserState.waiting_for_credentials.set()
    await state.update_data(command='cgpa_percentage')

async def handle_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    current_state = await state.get_state()
    print("Current state:", current_state)  # Debugging statement

    if current_state == 'UserState:waiting_for_credentials':
        username = message.text
        await message.answer("Please enter your password:")
        await UserState.next()  # Move to the next state
        await state.update_data(username=username)

    elif current_state == 'UserState:waiting_for_password':
        data = await state.get_data()
        print("State data:", data)  # Debugging statement
        username = data.get('username')
        password = message.text

        global driver
        try:
            if driver is None:
                await message.answer("Initializing... Please wait.")
                driver = await setup_driver()

            await login(driver, username, password)

            if is_dashboard_page(driver):
                await message.answer("Login successful. Retrieving data...")

                command = data.get('command')
                if command == 'cgpa':
                    cgpa_result = await scrape_cgpa(driver)
                    await message.answer(f"Your CGPA: {cgpa_result}")
                elif command == 'attendance':
                    attendance_result = await scrape_attendance(driver)
                    await message.answer(f"Your attendance: {attendance_result}")
                elif command == 'cgpa_percentage':
                    cgpa_percentage_result = await scrape_cgpa_percentage(driver)
                    await message.answer(f"Your CGPA percentage: {cgpa_percentage_result}")

            else:
                await message.answer("Login failed. Please check your credentials.")

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            await message.answer(f"An error occurred: {str(e)}")

        finally:
            if driver is not None:
                driver.quit()
            driver = None  # Reset the global driver variable

            await message.answer("Task completed!")
            await state.finish()  # Reset the user state

# Register handlers
dp.register_message_handler(start, commands=['start'])
dp.register_message_handler(cgpa, commands=['cgpa'])
dp.register_message_handler(attendance, commands=['attendance'])
dp.register_message_handler(cgpa_percentage, commands=['cgpa_percentage'])
dp.register_message_handler(handle_input, state=UserState.all_states)  # Handle all states

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, loop=loop)
