
def does_user_confirm() -> bool:
    choice = input("Please press Enter or input 'y' to confirm: ").strip().lower()
    confirmed = choice == '' or choice == 'y'
    if not confirmed:
        print("User cancelled.")
    return confirmed