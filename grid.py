from pprint import pprint
import random
import time
import copy

def solve_flood(grid):
    m = len(grid)
    n = len(grid[0])
    def flood_left(i,j):
        if j > 0 and grid[i][j-1] > 0:
            grid[i][j-1] += 1
    def flood_right(i,j):
        if j < n - 1 and grid[i][j+1] > 0:
            grid[i][j+1] += 1
    def flood_up(i,j):
        if i > 0 and grid[i-1][j] > 0:
            grid[i-1][j] += 1
    def flood_down(i,j):
        if i < m - 1 and grid[i+1][j] > 0:
            grid[i+1][j] += 1
    def flood_neighbors(i,j):
        flood_left(i,j)
        flood_up(i,j)
        flood_right(i,j)
        flood_down(i,j)

    c = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                c += 1
            if grid[i][j] > 0:
                flood_neighbors(i,j)
    return c

def solve_set(grid):
    m = len(grid)
    n = len(grid[0])
    checked = set()
    not_already_checked = lambda i,j: (i,j) not in checked
    def check_left(i,j):
        if j > 0 and not_already_checked(i,j-1) and grid[i][j-1] > 0:
            grid[i][j-1] += 1
        checked.add((i,j-1))
    def check_right(i,j):
        if j < n - 1 and not_already_checked(i,j+1) and grid[i][j+1] > 0:
            grid[i][j+1] += 1
        checked.add((i,j+1))
    def check_up(i,j):
        if i > 0 and not_already_checked(i-1,j) and grid[i-1][j] > 0:
            grid[i-1][j] += 1
        checked.add((i-1,j))
    def check_down(i,j):
        if i < m - 1 and not_already_checked(i+1,j) and grid[i+1][j] > 0:
            grid[i+1][j] += 1
        checked.add((i+1,j))
    def check(i,j):
        check_left(i,j)
        check_up(i,j)
        check_right(i,j)
        check_down(i,j)
    c = 0
    for i in range(m):
        for j in range(n):
            if grid[i][j] == 1:
                c += 1
            if grid[i][j] > 0:
                check(i,j)
    return c

t = [[1,1,0], [0,1,0], [1,0,1]]
iterations = 100

# Generate and test 10 large test cases
for test in range(10):
    # Create 100x100 grid with random 0s and 1s
    large_test = [[random.randint(0,1) for _ in range(100)] for _ in range(100)]
    
    # Time all solutions
    total_time_flood = 0
    total_time_set = 0
    total_time_dfs = 0
    
    # Run timing test
    for i in range(iterations):
        # Test flood fill solution
        test_grid = copy.deepcopy(large_test)
        start = time.time()
        a = solve_flood(test_grid)
        end = time.time()
        total_time_flood += (end - start)
        
        # Test set solution
        test_grid = copy.deepcopy(large_test)
        start = time.time()
        b = solve_set(test_grid)
        end = time.time()
        total_time_set += (end - start)



        if a != b:
            print('************************************************')
            print(i)
            print(a,b)
            print('---')
    # Calculate and display metrics
    avg_time_flood = total_time_flood / iterations
    avg_time_set = total_time_set / iterations
    
    print(f"\nTest case {test+1} metrics:")
    print("Flood Fill Solution:")
    print(f"Total time: {total_time_flood:.4f} seconds")
    print(f"Average time: {avg_time_flood:.4f} seconds")
    print(f"Iterations per second: {1/avg_time_flood:.2f}")
    
    print("\nSet Solution:")
    print(f"Total time: {total_time_set:.4f} seconds")
    print(f"Average time: {avg_time_set:.4f} seconds")
    print(f"Iterations per second: {1/avg_time_set:.2f}")

    
    print(f"\nFlood Fill solution is {total_time_set/total_time_flood:.2f}x faster than Set")

    print("-" * 50)