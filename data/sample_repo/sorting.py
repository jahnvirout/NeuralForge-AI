"""
Sorting Algorithms
"""


def bubble_sort(arr):
    """
    Sorts the array using Bubble Sort.

    Time Complexity:
        O(n²)
    """

    arr = arr.copy()

    n = len(arr)

    for i in range(n):

        swapped = False

        for j in range(0, n - i - 1):

            if arr[j] > arr[j + 1]:

                arr[j], arr[j + 1] = arr[j + 1], arr[j]

                swapped = True

        if not swapped:
            break

    return arr


def selection_sort(arr):
    """
    Sorts the array using Selection Sort.
    """

    arr = arr.copy()

    n = len(arr)

    for i in range(n):

        minimum = i

        for j in range(i + 1, n):

            if arr[j] < arr[minimum]:
                minimum = j

        arr[i], arr[minimum] = arr[minimum], arr[i]

    return arr


if __name__ == "__main__":

    numbers = [8, 2, 6, 1, 10, 3]

    print("Original :", numbers)

    print("Bubble Sort :", bubble_sort(numbers))

    print("Selection Sort :", selection_sort(numbers))