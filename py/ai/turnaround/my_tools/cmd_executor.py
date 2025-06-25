from smolagents import tool
import subprocess
import shlex

@tool
def cmd_executor(command: str, confirmed: bool = False) -> str:
    """
    This tool executes readonly shell commands in a Linux/macOS environment.
    It is restricted to safe, readonly commands that do not modify the filesystem
    or system state. Useful for exploring directory structures, searching files,
    and gathering information about the system.
    
    LIMITATION: Only readonly commands are allowed for security. Commands that
    modify files, install software, or change system state are blocked.
    
    Allowed commands include:
    - ls, find, locate, which, whereis
    - grep, egrep, fgrep, zgrep
    - cat, head, tail, less, more
    - wc, sort, uniq, cut, awk, sed (readonly operations)
    - ps, top, htop, df, du, free
    - pwd, whoami, id, uname, date
    - file, stat, lsof
    
    Args:
        command (str): The shell command to execute (must be readonly).
        confirmed (bool): Must be set to True to confirm command execution.
                         Defaults to False for safety.
    Returns:
        str: The output of the command or an error message.
    """
    # check if operation is confirmed
    if not confirmed:
        return "Error: Command execution not confirmed. Set confirmed=True to proceed with running the command."
    
    if not command.strip():
        return "No command provided."
    
    # List of allowed readonly commands
    allowed_commands = {
        'ls', 'find', 'locate', 'which', 'whereis',
        'grep', 'egrep', 'fgrep', 'zgrep', 'rg', 'ag',
        'cat', 'head', 'tail', 'less', 'more',
        'wc', 'sort', 'uniq', 'cut', 'awk', 'sed',
        'ps', 'top', 'htop', 'df', 'du', 'free',
        'pwd', 'whoami', 'id', 'uname', 'date',
        'file', 'stat', 'lsof', 'tree'
    }
    
    # Parse the command to get the base command
    try:
        parsed_command = shlex.split(command)
        base_command = parsed_command[0] if parsed_command else ""
    except ValueError:
        return "Error: Invalid command syntax."
    
    # Check if the base command is allowed
    if base_command not in allowed_commands:
        return f"Error: Command '{base_command}' is not allowed. Only readonly commands are permitted."
    
    # Additional safety checks for potentially dangerous flags
    dangerous_patterns = ['rm', 'mv', 'cp', 'chmod', 'chown', 'sudo', '>', '>>', '|', '&&', '||', ';']
    for pattern in dangerous_patterns:
        if pattern in command:
            return f"Error: Command contains potentially dangerous pattern '{pattern}'. Only readonly operations are allowed."
    
    try:
        # Execute the command with timeout for safety
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,  # 30 second timeout
            cwd=None  # Use current working directory
        )
        
        if result.returncode == 0:
            return result.stdout if result.stdout else "Command executed successfully (no output)."
        else:
            return f"Command failed with return code {result.returncode}:\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"An error occurred while executing the command: {str(e)}"