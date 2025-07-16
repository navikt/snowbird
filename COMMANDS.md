# Commands

```text
Usage: snowbird [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  apply
  plan
  save

Usage: snowbird plan [OPTIONS]

Options:
  --config TEXT     Path to the configuration file
  --silent          Silent mode. Can be used if you want to write the output
                    to a file
  --state TEXT      Path snowflake state file to compare against
  --stateless       Run without state comparison
  --execution-plan  Print the execution plan
  --help            Show this message and exit.

Usage: snowbird apply [OPTIONS]

Options:
  --config TEXT  Path to the configuration file
  --silent       Silent mode. Won't print the statements to the console
  --state TEXT   Path snowflake state file to compare against
  --stateless    Run without state comparison
  --help         Show this message and exit.

Usage: snowbird save [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  state

Usage: snowbird save state [OPTIONS]

Options:
  --file TEXT    Path to the file to write the state to
  --config TEXT  Path to the configuration file
  --help         Show this message and exit.

```
