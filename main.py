from team import job_helper_team


def main():
    print("Hello from jobhelperagents!")
    # Test run
    job_helper_team.print_response(
        "Find me 6 Senior Software Engineer, backend or embedded, roles in Seattle, WA", stream=True
    )


if __name__ == "__main__":
    main()
