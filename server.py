#!/usr/bin/env python3
"""
TiDB Custom MCP Server
Provides tools for interacting with TiDB database
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import pymysql
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


class TiDBConnection:
    """TiDB database connection manager"""
    
    def __init__(self):
        self.host = os.getenv("TIDB_HOST", "localhost")
        self.port = int(os.getenv("TIDB_PORT", "4000"))
        self.username = os.getenv("TIDB_USERNAME", "root")
        self.password = os.getenv("TIDB_PASSWORD", "")
        self.database = os.getenv("TIDB_DATABASE", "test")
        
    def get_connection(self):
        """Get a database connection"""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database,
            ssl={'ssl': True} if self.host != "localhost" else None,
            cursorclass=pymysql.cursors.DictCursor
        )


# Initialize the server
server = Server("tidb-custom-mcp")
db = TiDBConnection()


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="execute_sql",
            description="Execute SQL query on TiDB database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute"
                    },
                    "measure_time": {
                        "type": "boolean",
                        "description": "Whether to measure execution time",
                        "default": False
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_table_info",
            description="Get information about tables including size and row count",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table (optional, if not provided shows all tables)"
                    }
                }
            }
        ),
        Tool(
            name="get_database_stats",
            description="Get comprehensive database statistics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="benchmark_query",
            description="Run a query multiple times and measure average execution time",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to benchmark"
                    },
                    "iterations": {
                        "type": "integer",
                        "description": "Number of times to run the query",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    
    try:
        if name == "execute_sql":
            return await execute_sql(arguments)
        elif name == "get_table_info":
            return await get_table_info(arguments)
        elif name == "get_database_stats":
            return await get_database_stats(arguments)
        elif name == "benchmark_query":
            return await benchmark_query(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def execute_sql(arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute SQL query"""
    query = arguments["query"]
    measure_time = arguments.get("measure_time", False)
    
    connection = db.get_connection()
    try:
        cursor = connection.cursor()
        
        start_time = time.time() if measure_time else None
        cursor.execute(query)
        end_time = time.time() if measure_time else None
        
        # Handle different types of queries
        if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
            results = cursor.fetchall()
            result_text = f"Query executed successfully.\n"
            
            if measure_time:
                execution_time = (end_time - start_time) * 1000
                result_text += f"Execution time: {execution_time:.2f} ms\n"
            
            result_text += f"Rows returned: {len(results)}\n\n"
            
            if results:
                result_text += json.dumps(results, indent=2, default=str)
            else:
                result_text += "No rows returned."
                
        else:
            # For INSERT, UPDATE, DELETE, etc.
            connection.commit()
            affected_rows = cursor.rowcount
            result_text = f"Query executed successfully.\n"
            
            if measure_time:
                execution_time = (end_time - start_time) * 1000
                result_text += f"Execution time: {execution_time:.2f} ms\n"
            
            result_text += f"Affected rows: {affected_rows}"
        
        return [TextContent(type="text", text=result_text)]
        
    finally:
        connection.close()


async def get_table_info(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get table information"""
    table_name = arguments.get("table_name")
    
    connection = db.get_connection()
    try:
        cursor = connection.cursor()
        
        if table_name:
            # Get specific table info
            cursor.execute("""
                SELECT 
                    table_name,
                    table_rows,
                    data_length,
                    index_length,
                    (data_length + index_length) as total_size,
                    auto_increment,
                    table_comment
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = %s
            """, (db.database, table_name))
        else:
            # Get all tables info
            cursor.execute("""
                SELECT 
                    table_name,
                    table_rows,
                    data_length,
                    index_length,
                    (data_length + index_length) as total_size,
                    auto_increment,
                    table_comment
                FROM information_schema.tables 
                WHERE table_schema = %s
                ORDER BY total_size DESC
            """, (db.database,))
        
        results = cursor.fetchall()
        
        if not results:
            return [TextContent(type="text", text="No tables found.")]
        
        result_text = "Table Information:\n\n"
        
        for table in results:
            result_text += f"Table: {table['table_name']}\n"
            result_text += f"  Rows: {table['table_rows']:,}\n"
            result_text += f"  Data size: {table['data_length']:,} bytes ({table['data_length']/1024/1024:.2f} MB)\n"
            result_text += f"  Index size: {table['index_length']:,} bytes ({table['index_length']/1024/1024:.2f} MB)\n"
            result_text += f"  Total size: {table['total_size']:,} bytes ({table['total_size']/1024/1024:.2f} MB)\n"
            if table['auto_increment']:
                result_text += f"  Auto increment: {table['auto_increment']}\n"
            if table['table_comment']:
                result_text += f"  Comment: {table['table_comment']}\n"
            result_text += "\n"
        
        return [TextContent(type="text", text=result_text)]
        
    finally:
        connection.close()


async def get_database_stats(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get comprehensive database statistics"""
    connection = db.get_connection()
    try:
        cursor = connection.cursor()
        
        # Database basic info
        cursor.execute("SELECT DATABASE() as current_db, VERSION() as version")
        db_info = cursor.fetchone()
        
        # Total tables and size
        cursor.execute("""
            SELECT 
                COUNT(*) as table_count,
                SUM(table_rows) as total_rows,
                SUM(data_length) as total_data_size,
                SUM(index_length) as total_index_size,
                SUM(data_length + index_length) as total_size
            FROM information_schema.tables 
            WHERE table_schema = %s
        """, (db.database,))
        
        stats = cursor.fetchone()
        
        # Connection info
        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        connections = cursor.fetchone()
        
        result_text = f"Database Statistics\n"
        result_text += f"==================\n\n"
        result_text += f"Database: {db_info['current_db']}\n"
        result_text += f"Version: {db_info['version']}\n"
        result_text += f"Host: {db.host}:{db.port}\n\n"
        
        result_text += f"Table Statistics:\n"
        result_text += f"  Total tables: {stats['table_count']}\n"
        result_text += f"  Total rows: {stats['total_rows']:,}\n"
        result_text += f"  Data size: {stats['total_data_size']:,} bytes ({stats['total_data_size']/1024/1024:.2f} MB)\n"
        result_text += f"  Index size: {stats['total_index_size']:,} bytes ({stats['total_index_size']/1024/1024:.2f} MB)\n"
        result_text += f"  Total size: {stats['total_size']:,} bytes ({stats['total_size']/1024/1024:.2f} MB)\n\n"
        
        if connections:
            result_text += f"Active connections: {connections['Value']}\n"
        
        return [TextContent(type="text", text=result_text)]
        
    finally:
        connection.close()


async def benchmark_query(arguments: Dict[str, Any]) -> List[TextContent]:
    """Benchmark a query by running it multiple times"""
    query = arguments["query"]
    iterations = arguments.get("iterations", 5)
    
    if iterations > 50:
        iterations = 50
    
    times = []
    connection = db.get_connection()
    
    try:
        cursor = connection.cursor()
        
        # Warm-up run
        cursor.execute(query)
        if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
            cursor.fetchall()
        
        # Benchmark runs
        for i in range(iterations):
            start_time = time.time()
            cursor.execute(query)
            if query.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                results = cursor.fetchall()
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            times.append(execution_time)
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        result_text = f"Query Benchmark Results\n"
        result_text += f"======================\n\n"
        result_text += f"Query: {query}\n"
        result_text += f"Iterations: {iterations}\n\n"
        result_text += f"Average execution time: {avg_time:.2f} ms\n"
        result_text += f"Minimum execution time: {min_time:.2f} ms\n"
        result_text += f"Maximum execution time: {max_time:.2f} ms\n\n"
        result_text += f"Individual times: {[f'{t:.2f}' for t in times]} ms\n"
        
        return [TextContent(type="text", text=result_text)]
        
    finally:
        connection.close()


async def main():
    """Main server function"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())