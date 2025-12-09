from team import job_helper_team


def main():
    print("Hello from jobhelperagents!")
    # Test run
    job_helper_team.print_response(
        "Find me 3 Senior Python Developer roles in Austin, TX", stream=True
    )


if __name__ == "__main__":
    main()
