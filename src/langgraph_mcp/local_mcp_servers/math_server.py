from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers
    
    Args:
        a: first int
        b: second int
        
    Example:
        >>> add(1, 2)
        3
    
    Returns: int: sum of a and b    
    """
    
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply a and b.

    Args:
        a: first int
        b: second int
        
    Example:
        >>> multiply(2, 3)
        6
    
    Returns: int: product of a and b
    """
    return a * b


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers

    Args:
        a: first float
        b: second float
    Example:
        >>> divide(10, 2)
        5.0
    
    Returns: float: quotient of a and b 
    """
    return a / b


if __name__ == "__main__":
    mcp.run(transport="stdio")
