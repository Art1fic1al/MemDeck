def ynr(answer):
    if answer == "y":
        print("\nProceeding\n")
        return True
    elif answer == "n":
        print("\nCancelling\n")
        exit()
    elif answer == "r":
        print("\nRedoing Input\n")
        return False
    else:
        print(f"The answer \"{answer}\" is not a valid answer. Please input only the aforementioned characters.\n")
        return False


def yn(answer):
    if answer == "y":
        print("\nProceeding\n")
        return True
    elif answer == "n":
        print("\nCancelling\n")
        exit()
    else:
        print(f"The answer \"{answer}\" is not a valid answer. Please input only the aforementioned characters.\n")
        return False