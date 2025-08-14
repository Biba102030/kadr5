from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import AuthStates
from user_manager import UserManager
from keyboards import get_main_menu

user_manager = UserManager()

def register_registration_handlers(dp: Dispatcher):
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        user_id = str(message.from_user.id)
        user = user_manager.get_user(user_id)
        if user:
            await message.answer(
                f"Добро пожаловать обратно, {user['name']}! 👋",
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                "Добро пожаловать! 👋\n\nДля использования бота необходимо пройти регистрацию.\nПожалуйста, введите ваше имя:"
            )
            await state.set_state(AuthStates.WAITING_FOR_NAME)

    @dp.message(AuthStates.WAITING_FOR_NAME)
    async def process_name(message: types.Message, state: FSMContext):
        name = message.text.strip()
        if len(name) < 2:
            await message.answer("Имя должно содержать минимум 2 символа. Попробуйте снова:")
            return
        await state.update_data(name=name)
        await message.answer("Теперь введите ваш номер телефона:")
        await state.set_state(AuthStates.WAITING_FOR_PHONE)

    @dp.message(AuthStates.WAITING_FOR_PHONE)
    async def process_phone(message: types.Message, state: FSMContext):
        phone = message.text.strip()
        if len(phone) < 9:
            await message.answer("Некорректный номер телефона. Попробуйте снова:")
            return
        user_id = str(message.from_user.id)
        data = await state.get_data()
        user_manager.add_user(user_id, data["name"], phone)
        await message.answer(
            f"✅ Регистрация завершена, {data['name']}!\n\nТеперь вы можете пользоваться всеми функциями бота.",
            reply_markup=get_main_menu()
        )
        await state.clear()