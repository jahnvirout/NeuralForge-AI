"""
Searching Algorithms
"""


def linear_search(arr, target):
    """
    Searches for the target using Linear Search.

    Returns:
        Index of target if found, else -1.
    """

    for index, value in enumerate(arr):
        if value == target:
            return index

    return -1


def binary_search(arr, target):
    """
    Searches for the target using Binary Search.

    Note:
        Array must be sorted.

    Returns:
        Index of target if found, else -1.
    """

    left = 0
    right = len(arr) - 1

    while left <= right:

        mid = (left + right) // 2

        if arr[mid] == target:
            return mid

        elif arr[mid] < target:
            left = mid + 1

        else:
            right = mid - 1

    return -1


if __name__ == "__main__":
    numbers = [2, 5, 7, 10, 15, 20, 30]

    print("Linear Search:", linear_search(numbers, 15))
    print("Binary Search:", binary_search(numbers, 15))