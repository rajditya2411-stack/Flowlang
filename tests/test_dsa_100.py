import sys
import os

sys.path.insert(0, os.path.abspath("src"))
from flowlang.engine import execute

# 100 DSA Problems in FlowLang V2 Hardened
# Complete, strictly compliant benchmark

problems = [
    # ==========================================
    # Category 1: Basic Arrays, Loops & Math (1-10)
    # ==========================================
    (1, "Linear Search", """
    dfn linear_search(list arr, int target) -> int {
        for i in (0; i < len_(arr); i = i + 1) {
            if arr[i] == target {
                return i;
            }
        }
        return -1;
    }
    say(linear_search([10, 20, 30, 40, 50], 30));
    say(linear_search([10, 20, 30, 40, 50], 99));
    """, "2\n-1"),

    (2, "Array Reverse In-Place", """
    dfn reverse_arr(list arr) -> list {
        mut int left = 0;
        mut int right = len_(arr) - 1;
        while left < right {
            int tmp = arr[left];
            arr[left] = arr[right];
            arr[right] = tmp;
            left = left + 1;
            right = right - 1;
        }
        return arr;
    }
    say(reverse_arr([1, 2, 3, 4, 5]));
    """, "[5, 4, 3, 2, 1]"),

    (3, "Running Sum of 1D Array", """
    dfn running_sum(list nums) -> list {
        list res = [];
        mut int cur = 0;
        for x in nums {
            cur = cur + int_(x);
            append_(res, cur);
        }
        return res;
    }
    say(running_sum([1, 2, 3, 4]));
    """, "[1, 3, 6, 10]"),

    (4, "Find Max and Min", """
    dfn find_max_min(list nums) -> brack {
        mut int mx = nums[0];
        mut int mn = nums[0];
        for x in nums {
            int v = int_(x);
            if v > mx { mx = v; }
            if v < mn { mn = v; }
        }
        return (mx, mn);
    }
    say(find_max_min([3, 1, 9, -2, 7]));
    """, "(9, -2)"),

    (5, "Second Largest Element", """
    dfn second_largest(list nums) -> int {
        mut int first = -2147483648;
        mut int second = -2147483648;
        for x in nums {
            int v = int_(x);
            if v > first {
                second = first;
                first = v;
            } elif v > second and v != first {
                second = v;
            }
        }
        return second;
    }
    say(second_largest([12, 35, 1, 10, 34, 1]));
    """, "34"),

    (6, "Partition Even and Odd", """
    dfn partition_even_odd(list nums) -> list {
        list evens = [];
        list odds = [];
        for x in nums {
            int v = int_(x);
            if v % 2 == 0 {
                append_(evens, v);
            } else {
                append_(odds, v);
            }
        }
        for o in odds {
            append_(evens, int_(o));
        }
        return evens;
    }
    say(partition_even_odd([1, 2, 3, 4, 5, 6]));
    """, "[2, 4, 6, 1, 3, 5]"),

    (7, "Palindrome Number", """
    dfn is_palindrome(int x) -> bool {
        if x < 0 { return false; }
        int orig = x;
        mut int temp = x;
        mut int rev = 0;
        while temp > 0 {
            int digit = temp % 10;
            rev = rev * 10 + digit;
            temp = temp // 10;
        }
        return rev == orig;
    }
    say(is_palindrome(121));
    say(is_palindrome(-121));
    say(is_palindrome(10));
    """, "true\nfalse\nfalse"),

    (8, "Prime Number Check", """
    dfn is_prime(int n) -> bool {
        if n <= 1 { return false; }
        mut int i = 2;
        while i * i <= n {
            if n % i == 0 { return false; }
            i = i + 1;
        }
        return true;
    }
    say(is_prime(29));
    say(is_prime(15));
    """, "true\nfalse"),

    (9, "Factorial (Iterative)", """
    dfn fact(int n) -> int {
        mut int res = 1;
        mut int i = 1;
        while i <= n {
            res = res * i;
            i = i + 1;
        }
        return res;
    }
    say(fact(5));
    """, "120"),

    (10, "GCD (Euclidean Algorithm)", """
    dfn gcd(int a, int b) -> int {
        mut int x = a;
        mut int y = b;
        while y != 0 {
            int t = y;
            y = x % y;
            x = t;
        }
        return x;
    }
    say(gcd(48, 18));
    """, "6"),

    # ==========================================
    # Category 2: Two Pointers & Strings (11-20)
    # ==========================================
    (11, "Valid Palindrome String", """
    dfn is_pal_str(str s) -> bool {
        mut int l = 0;
        mut int r = len_(s) - 1;
        while l < r {
            if s[l] != s[r] {
                return false;
            }
            l = l + 1;
            r = r - 1;
        }
        return true;
    }
    say(is_pal_str("racecar"));
    say(is_pal_str("hello"));
    """, "true\nfalse"),

    (12, "Two Sum II (Sorted Array)", """
    dfn two_sum_sorted(list nums, int target) -> brack {
        int l = 0;
        mut int r = len_(nums) - 1;
        while l < r {
            int sum_val = nums[l] + nums[r];
            if sum_val == target {
                return (l, r);
            } elif sum_val < target {
                l = l + 1;
            } else {
                r = r - 1;
            }
        }
        return (-1, -1);
    }
    say(two_sum_sorted([2, 7, 11, 15], 9));
    """, "(0, 1)"),

    (13, "Remove Duplicates from Sorted Array", """
    dfn remove_duplicates(list nums) -> int {
        if len_(nums) == 0 { return 0; }
        mut int insert_idx = 1;
        for i in (1; i < len_(nums); i = i + 1) {
            if nums[i] != nums[i - 1] {
                nums[insert_idx] = nums[i];
                insert_idx = insert_idx + 1;
            }
        }
        return insert_idx;
    }
    list a = [1, 1, 2, 2, 3, 4, 4];
    int k = remove_duplicates(a);
    say(k);
    """, "4"),

    (14, "Move Zeroes", """
    dfn move_zeroes(list nums) -> list {
        mut int insert_pos = 0;
        for i in (0; i < len_(nums); i = i + 1) {
            if nums[i] != 0 {
                nums[insert_pos] = nums[i];
                insert_pos = insert_pos + 1;
            }
        }
        while insert_pos < len_(nums) {
            nums[insert_pos] = 0;
            insert_pos = insert_pos + 1;
        }
        return nums;
    }
    say(move_zeroes([0, 1, 0, 3, 12]));
    """, "[1, 3, 12, 0, 0]"),

    (15, "Container With Most Water", """
    dfn max_area(list height) -> int {
        mut int l = 0;
        mut int r = len_(height) - 1;
        mut int max_val = 0;
        while l < r {
            mut int h = height[l];
            if height[r] < h { h = height[r]; }
            int area = h * (r - l);
            if area > max_val { max_val = area; }
            if height[l] < height[r] {
                l = l + 1;
            } else {
                r = r - 1;
            }
        }
        return max_val;
    }
    say(max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]));
    """, "49"),

    (16, "Reverse String In-Place Representation", """
    dfn reverse_string(str s) -> str {
        mut str res = "";
        mut int i = len_(s) - 1;
        while i >= 0 {
            res = res + s[i];
            i = i - 1;
        }
        return res;
    }
    say(reverse_string("flowlang"));
    """, "gnalwolf"),

    (17, "Count Vowels and Consonants", """
    dfn count_vowels(str s) -> brack {
        mut int vowels = 0;
        mut int consonants = 0;
        for i in (0; i < len_(s); i = i + 1) {
            str c = s[i];
            if c == "a" or c == "e" or c == "i" or c == "o" or c == "u" {
                vowels = vowels + 1;
            } else {
                consonants = consonants + 1;
            }
        }
        return (vowels, consonants);
    }
    say(count_vowels("apple"));
    """, "(2, 3)"),

    (18, "String Compression Simulation", """
    dfn compress_chars(str s) -> str {
        if len_(s) == 0 { return ""; }
        mut str res = "";
        mut int count = 1;
        for i in (1; i < len_(s); i = i + 1) {
            if s[i] == s[i - 1] {
                count = count + 1;
            } else {
                res = res + s[i - 1] + str_(count);
                count = 1;
            }
        }
        res = res + s[len_(s) - 1] + str_(count);
        return res;
    }
    say(compress_chars("aabcccccaaa"));
    """, "a2b1c5a3"),

    (19, "Squares of a Sorted Array", """
    dfn sorted_squares(list nums) -> list {
        int n = len_(nums);
        list res = [];
        for i in (0; i < n; i = i + 1) {
            append_(res, 0);
        }
        mut int l = 0;
        mut int r = n - 1;
        mut int p = n - 1;
        while l <= r {
            int left_sq = nums[l] * nums[l];
            int right_sq = nums[r] * nums[r];
            if left_sq > right_sq {
                res[p] = left_sq;
                l = l + 1;
            } else {
                res[p] = right_sq;
                r = r - 1;
            }
            p = p - 1;
        }
        return res;
    }
    say(sorted_squares([-4, -1, 0, 3, 10]));
    """, "[0, 1, 9, 16, 100]"),

    (20, "3Sum Zero Check", """
    dfn has_three_sum_zero(list nums) -> bool {
        int n = len_(nums);
        for i in (0; i < n; i = i + 1) {
            for j in (i + 1; j < n; j = j + 1) {
                for k in (j + 1; k < n; k = k + 1) {
                    if nums[i] + nums[j] + nums[k] == 0 {
                        return true;
                    }
                }
            }
        }
        return false;
    }
    say(has_three_sum_zero([-1, 0, 1, 2, -1, -4]));
    say(has_three_sum_zero([1, 2, 3]));
    """, "true\nfalse"),

    # ==========================================
    # Category 3: Sliding Window & Prefix Sums (21-30)
    # ==========================================
    (21, "Maximum Subarray Sum (Kadane's Algorithm)", """
    dfn max_sub_array(list nums) -> int {
        mut int max_so_far = nums[0];
        mut int curr_max = nums[0];
        for i in (1; i < len_(nums); i = i + 1) {
            int v = nums[i];
            if curr_max + v > v {
                curr_max = curr_max + v;
            } else {
                curr_max = v;
            }
            if curr_max > max_so_far {
                max_so_far = curr_max;
            }
        }
        return max_so_far;
    }
    say(max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]));
    """, "6"),

    (22, "Max Sum Subarray of Size K", """
    dfn max_sum_k(list nums, int k) -> int {
        mut int win_sum = 0;
        for i in (0; i < k; i = i + 1) {
            win_sum = win_sum + nums[i];
        }
        mut int max_sum = win_sum;
        for i in (k; i < len_(nums); i = i + 1) {
            win_sum = win_sum + nums[i] - nums[i - k];
            if win_sum > max_sum {
                max_sum = win_sum;
            }
        }
        return max_sum;
    }
    say(max_sum_k([2, 1, 5, 1, 3, 2], 3));
    """, "9"),

    (23, "Minimum Size Subarray Sum", """
    dfn min_sub_array_len(int target, list nums) -> int {
        int n = len_(nums);
        mut int min_len = 2147483647;
        mut int left = 0;
        mut int cur_sum = 0;
        for right in (0; right < n; right = right + 1) {
            cur_sum = cur_sum + nums[right];
            while cur_sum >= target {
                int cur_len = right - left + 1;
                if cur_len < min_len { min_len = cur_len; }
                cur_sum = cur_sum - nums[left];
                left = left + 1;
            }
        }
        if min_len == 2147483647 { return 0; }
        return min_len;
    }
    say(min_sub_array_len(7, [2, 3, 1, 2, 4, 3]));
    """, "2"),

    (24, "Longest Substring Without Repeating Chars", """
    import flowlib;
    dfn length_of_longest_substring(str s) -> int {
        dict char_idx = << >>;
        mut int max_len = 0;
        mut int left = 0;
        for right in (0; right < len_(s); right = right + 1) {
            str c = s[right];
            int prev_idx = get_(char_idx, c, -1);
            if prev_idx >= left {
                left = prev_idx + 1;
            }
            char_idx[c] = right;
            int cur_len = right - left + 1;
            if cur_len > max_len { max_len = cur_len; }
        }
        return max_len;
    }
    say(length_of_longest_substring("abcabcbb"));
    say(length_of_longest_substring("bbbbb"));
    """, "3\n1"),

    (25, "Subarray Sum Equals K (Frequency Map)", """
    import flowlib;
    dfn subarray_sum(list nums, int k) -> int {
        dict prefix_counts = << 0 : 1 >>;
        mut int count = 0;
        mut int cur_sum = 0;
        for i in (0; i < len_(nums); i = i + 1) {
            cur_sum = cur_sum + nums[i];
            int diff = cur_sum - k;
            int diff_count = get_(prefix_counts, diff, 0);
            count = count + diff_count;
            int prev = get_(prefix_counts, cur_sum, 0);
            prefix_counts[cur_sum] = prev + 1;
        }
        return count;
    }
    say(subarray_sum([1, 1, 1], 2));
    say(subarray_sum([1, 2, 3], 3));
    """, "2\n2"),

    (26, "Product of Array Except Self", """
    dfn product_except_self(list nums) -> list {
        int n = len_(nums);
        list res = [];
        for i in (0; i < n; i = i + 1) { append_(res, 1); }
        mut int prefix = 1;
        for i in (0; i < n; i = i + 1) {
            res[i] = prefix;
            prefix = prefix * nums[i];
        }
        mut int suffix = 1;
        mut int j = n - 1;
        while j >= 0 {
            res[j] = res[j] * suffix;
            suffix = suffix * nums[j];
            j = j - 1;
        }
        return res;
    }
    say(product_except_self([1, 2, 3, 4]));
    """, "[24, 12, 8, 6]"),

    (27, "Maximum Product Subarray", """
    dfn max_product(list nums) -> int {
        mut int max_prod = nums[0];
        mut int cur_min = nums[0];
        mut int cur_max = nums[0];
        for i in (1; i < len_(nums); i = i + 1) {
            int x = nums[i];
            int c1 = cur_max * x;
            int c2 = cur_min * x;
            mut int new_max = x;
            if c1 > new_max { new_max = c1; }
            if c2 > new_max { new_max = c2; }
            mut int new_min = x;
            if c1 < new_min { new_min = c1; }
            if c2 < new_min { new_min = c2; }
            cur_max = new_max;
            cur_min = new_min;
            if cur_max > max_prod { max_prod = cur_max; }
        }
        return max_prod;
    }
    say(max_product([2, 3, -2, 4]));
    """, "6"),

    (28, "Find Pivot Index", """
    dfn pivot_index(list nums) -> int {
        mut int total = 0;
        for x in nums { total = total + int_(x); }
        mut int left_sum = 0;
        for i in (0; i < len_(nums); i = i + 1) {
            if left_sum == (total - left_sum - nums[i]) {
                return i;
            }
            left_sum = left_sum + nums[i];
        }
        return -1;
    }
    say(pivot_index([1, 7, 3, 6, 5, 6]));
    """, "3"),

    (29, "Find All Numbers Disappeared in Array", """
    dfn find_disappeared(list nums) -> list {
        list present = [];
        int n = len_(nums);
        for i in (0; i <= n; i = i + 1) { append_(present, false); }
        for x in nums {
            present[int_(x)] = true;
        }
        list res = [];
        for i in (1; i <= n; i = i + 1) {
            if not present[i] {
                append_(res, i);
            }
        }
        return res;
    }
    say(find_disappeared([4, 3, 2, 7, 8, 2, 3, 1]));
    """, "[5, 6]"),

    (30, "Majority Element (Boyer-Moore Voting)", """
    dfn majority_element(list nums) -> int {
        mut int count = 0;
        mut int candidate = 0;
        for x in nums {
            int v = int_(x);
            if count == 0 {
                candidate = v;
            }
            if v == candidate {
                count = count + 1;
            } else {
                count = count - 1;
            }
        }
        return candidate;
    }
    say(majority_element([2, 2, 1, 1, 1, 2, 2]));
    """, "2"),

    # ==========================================
    # Category 4: Sorting & Binary Search (31-40)
    # ==========================================
    (31, "Binary Search (Iterative)", """
    dfn binary_search(list nums, int target) -> int {
        mut int l = 0;
        mut int r = len_(nums) - 1;
        while l <= r {
            int mid = l + (r - l) // 2;
            if nums[mid] == target {
                return mid;
            } elif nums[mid] < target {
                l = mid + 1;
            } else {
                r = mid - 1;
            }
        }
        return -1;
    }
    say(binary_search([-1, 0, 3, 5, 9, 12], 9));
    say(binary_search([-1, 0, 3, 5, 9, 12], 2));
    """, "4\n-1"),

    (32, "Search Insert Position", """
    dfn search_insert(list nums, int target) -> int {
        mut int l = 0;
        mut int r = len_(nums) - 1;
        while l <= r {
            int mid = l + (r - l) // 2;
            if nums[mid] == target {
                return mid;
            } elif nums[mid] < target {
                l = mid + 1;
            } else {
                r = mid - 1;
            }
        }
        return l;
    }
    say(search_insert([1, 3, 5, 6], 5));
    say(search_insert([1, 3, 5, 6], 2));
    say(search_insert([1, 3, 5, 6], 7));
    """, "2\n1\n4"),

    (33, "Find First and Last Position in Sorted Array", """
    dfn find_bound(list nums, int target, bool is_first) -> int {
        mut int l = 0;
        mut int r = len_(nums) - 1;
        mut int ans = -1;
        while l <= r {
            int mid = l + (r - l) // 2;
            if nums[mid] == target {
                ans = mid;
                if is_first {
                    r = mid - 1;
                } else {
                    l = mid + 1;
                }
            } elif nums[mid] < target {
                l = mid + 1;
            } else {
                r = mid - 1;
            }
        }
        return ans;
    }
    dfn search_range(list nums, int target) -> brack {
        return (find_bound(nums, target, true), find_bound(nums, target, false));
    }
    say(search_range([5, 7, 7, 8, 8, 10], 8));
    say(search_range([5, 7, 7, 8, 8, 10], 6));
    """, "(3, 4)\n(-1, -1)"),

    (34, "Square Root via Binary Search", """
    dfn my_sqrt(int x) -> int {
        if x < 2 { return x; }
        mut int l = 1;
        mut int r = x // 2;
        mut int ans = 0;
        while l <= r {
            int mid = l + (r - l) // 2;
            if mid <= x // mid {
                ans = mid;
                l = mid + 1;
            } else {
                r = mid - 1;
            }
        }
        return ans;
    }
    say(my_sqrt(8));
    say(my_sqrt(16));
    """, "2\n4"),

    (35, "Bubble Sort", """
    dfn bubble_sort(list nums) -> list {
        int n = len_(nums);
        for i in (0; i < n; i = i + 1) {
            for j in (0; j < n - i - 1; j = j + 1) {
                if nums[j] > nums[j + 1] {
                    int tmp = nums[j];
                    nums[j] = nums[j + 1];
                    nums[j + 1] = tmp;
                }
            }
        }
        return nums;
    }
    say(bubble_sort([64, 34, 25, 12, 22, 11, 90]));
    """, "[11, 12, 22, 25, 34, 64, 90]"),

    (36, "Selection Sort", """
    dfn selection_sort(list nums) -> list {
        int n = len_(nums);
        for i in (0; i < n; i = i + 1) {
            mut int min_idx = int_(i);
            for j in (i + 1; j < n; j = j + 1) {
                if nums[j] < nums[min_idx] {
                    min_idx = int_(j);
                }
            }
            int tmp = nums[i];
            nums[i] = nums[min_idx];
            nums[min_idx] = tmp;
        }
        return nums;
    }
    say(selection_sort([29, 10, 14, 37, 13]));
    """, "[10, 13, 14, 29, 37]"),

    (37, "Insertion Sort", """
    dfn insertion_sort(list nums) -> list {
        int n = len_(nums);
        for i in (1; i < n; i = i + 1) {
            int key = nums[i];
            mut int j = i - 1;
            while j >= 0 and nums[j] > key {
                nums[j + 1] = nums[j];
                j = j - 1;
            }
            nums[j + 1] = key;
        }
        return nums;
    }
    say(insertion_sort([12, 11, 13, 5, 6]));
    """, "[5, 6, 11, 12, 13]"),

    (38, "Search in Rotated Sorted Array", """
    dfn search_rotated(list nums, int target) -> int {
        mut int l = 0;
        mut int r = len_(nums) - 1;
        while l <= r {
            int mid = l + (r - l) // 2;
            if nums[mid] == target { return mid; }
            if nums[l] <= nums[mid] {
                if nums[l] <= target and target < nums[mid] {
                    r = mid - 1;
                } else {
                    l = mid + 1;
                }
            } else {
                if nums[mid] < target and target <= nums[r] {
                    l = mid + 1;
                } else {
                    r = mid - 1;
                }
            }
        }
        return -1;
    }
    say(search_rotated([4, 5, 6, 7, 0, 1, 2], 0));
    say(search_rotated([4, 5, 6, 7, 0, 1, 2], 3));
    """, "4\n-1"),

    (39, "Find Peak Element", """
    dfn find_peak(list nums) -> int {
        mut int l = 0;
        mut int r = len_(nums) - 1;
        while l < r {
            int mid = l + (r - l) // 2;
            if nums[mid] > nums[mid + 1] {
                r = mid;
            } else {
                l = mid + 1;
            }
        }
        return l;
    }
    say(find_peak([1, 2, 3, 1]));
    """, "2"),

    (40, "Merge Sort (Recursive)", """
    dfn merge(list left, list right) -> list {
        list res = [];
        mut int i = 0;
        mut int j = 0;
        while i < len_(left) and j < len_(right) {
            if left[i] <= right[j] {
                append_(res, left[i]);
                i = i + 1;
            } else {
                append_(res, right[j]);
                j = j + 1;
            }
        }
        while i < len_(left) { append_(res, left[i]); i = i + 1; }
        while j < len_(right) { append_(res, right[j]); j = j + 1; }
        return res;
    }
    dfn merge_sort(list nums) -> list {
        if len_(nums) <= 1 { return nums; }
        int mid = len_(nums) // 2;
        list left = [];
        list right = [];
        for i in (0; i < mid; i = i + 1) { append_(left, nums[i]); }
        for i in (mid; i < len_(nums); i = i + 1) { append_(right, nums[i]); }
        return merge(merge_sort(left), merge_sort(right));
    }
    say(merge_sort([38, 27, 43, 3, 9, 82, 10]));
    """, "[3, 9, 10, 27, 38, 43, 82]"),

    # ==========================================
    # Category 5: Hash Maps & Frequency Counting (41-50)
    # ==========================================
    (41, "Two Sum (Hash Map)", """
    import flowlib;
    dfn two_sum(list nums, int target) -> brack {
        dict map_val = << >>;
        for i in (0; i < len_(nums); i = i + 1) {
            int comp = target - nums[i];
            int comp_idx = get_(map_val, comp, -1);
            if comp_idx != -1 {
                return (comp_idx, i);
            }
            map_val[nums[i]] = i;
        }
        return (-1, -1);
    }
    say(two_sum([2, 7, 11, 15], 9));
    """, "(0, 1)"),

    (42, "Valid Anagram", """
    import flowlib;
    dfn is_anagram(str s, str t) -> bool {
        if len_(s) != len_(t) { return false; }
        dict count = << >>;
        for i in (0; i < len_(s); i = i + 1) {
            str c = s[i];
            int cur = get_(count, c, 0);
            count[c] = cur + 1;
        }
        for i in (0; i < len_(t); i = i + 1) {
            str c = t[i];
            int cur = get_(count, c, 0);
            if cur == 0 { return false; }
            count[c] = cur - 1;
        }
        return true;
    }
    say(is_anagram("anagram", "nagaram"));
    say(is_anagram("rat", "car"));
    """, "true\nfalse"),

    (43, "First Unique Character in String", """
    import flowlib;
    dfn first_uniq_char(str s) -> int {
        dict counts = << >>;
        for i in (0; i < len_(s); i = i + 1) {
            str c = s[i];
            int cur = get_(counts, c, 0);
            counts[c] = cur + 1;
        }
        for i in (0; i < len_(s); i = i + 1) {
            if counts[s[i]] == 1 { return i; }
        }
        return -1;
    }
    say(first_uniq_char("flowlang"));
    say(first_uniq_char("aabb"));
    """, "0\n-1"),

    (44, "Intersection of Two Arrays", """
    import flowlib;
    dfn intersection(list nums1, list nums2) -> list {
        dict set1 = << >>;
        for x in nums1 { set1[int_(x)] = true; }
        dict res_set = << >>;
        for x in nums2 {
            int v = int_(x);
            bool in_set = get_(set1, v, false);
            if in_set { res_set[v] = true; }
        }
        list res = [];
        for k in res_set.keys { append_(res, k); }
        return res;
    }
    say(intersection([1, 2, 2, 1], [2, 2]));
    """, "[2]"),

    (45, "Longest Consecutive Sequence Length", """
    import flowlib;
    dfn longest_consecutive(list nums) -> int {
        dict num_set = << >>;
        for x in nums { num_set[int_(x)] = true; }
        mut int longest = 0;
        for x in nums {
            int v = int_(x);
            bool has_prev = get_(num_set, v - 1, false);
            if not has_prev {
                mut int cur_num = v;
                mut int cur_streak = 1;
                while get_(num_set, cur_num + 1, false) {
                    cur_num = cur_num + 1;
                    cur_streak = cur_streak + 1;
                }
                if cur_streak > longest { longest = cur_streak; }
            }
        }
        return longest;
    }
    say(longest_consecutive([100, 4, 200, 1, 3, 2]));
    """, "4"),

    (46, "Find Dispersed Single Number (XOR simulation / Hashing)", """
    import flowlib;
    dfn single_number(list nums) -> int {
        dict count = << >>;
        for x in nums {
            int v = int_(x);
            int c = get_(count, v, 0);
            count[v] = c + 1;
        }
        for k in count.keys {
            if count[k] == 1 { return int_(k); }
        }
        return -1;
    }
    say(single_number([4, 1, 2, 1, 2]));
    """, "4"),

    (47, "Ransom Note Constructible", """
    import flowlib;
    dfn can_construct(str ransom_note, str magazine) -> bool {
        dict counts = << >>;
        for i in (0; i < len_(magazine); i = i + 1) {
            str c = magazine[i];
            int cur = get_(counts, c, 0);
            counts[c] = cur + 1;
        }
        for i in (0; i < len_(ransom_note); i = i + 1) {
            str c = ransom_note[i];
            int cur = get_(counts, c, 0);
            if cur <= 0 { return false; }
            counts[c] = cur - 1;
        }
        return true;
    }
    say(can_construct("aa", "aab"));
    say(can_construct("aa", "ab"));
    """, "true\nfalse"),

    (48, "Group Anagrams Check", """
    import flowlib;
    dfn are_grouped(str a, str b) -> bool {
        if len_(a) != len_(b) { return false; }
        dict ca = << >>;
        dict cb = << >>;
        for i in (0; i < len_(a); i = i + 1) {
            str x = a[i];
            ca[x] = get_(ca, x, 0) + 1;
            str y = b[i];
            cb[y] = get_(cb, y, 0) + 1;
        }
        for k in ca.keys {
            if get_(ca, k, 0) != get_(cb, k, 0) { return false; }
        }
        return true;
    }
    say(are_grouped("eat", "tea"));
    say(are_grouped("eat", "tan"));
    """, "true\nfalse"),

    (49, "Subarray Sums Divisible by K", """
    import flowlib;
    dfn subarrays_div_by_k(list nums, int k) -> int {
        dict mod_counts = << 0 : 1 >>;
        mut int prefix = 0;
        mut int res = 0;
        for i in (0; i < len_(nums); i = i + 1) {
            prefix = prefix + nums[i];
            int rem = prefix % k;
            if rem < 0 { rem = rem + k; }
            int c = get_(mod_counts, rem, 0);
            res = res + c;
            mod_counts[rem] = c + 1;
        }
        return res;
    }
    say(subarrays_div_by_k([4, 5, 0, -2, -3, 1], 5));
    """, "7"),

    (50, "Most Frequent Element", """
    import flowlib;
    dfn most_frequent(list nums) -> int {
        dict freq = << >>;
        for x in nums {
            int v = int_(x);
            freq[v] = get_(freq, v, 0) + 1;
        }
        mut int max_count = 0;
        mut int best_el = nums[0];
        for k in freq.keys {
            int c = int_(freq[k]);
            if c > max_count {
                max_count = c;
                best_el = int_(k);
            }
        }
        return best_el;
    }
    say(most_frequent([1, 3, 2, 1, 4, 1]));
    """, "1"),

    # ==========================================
    # Category 6: Stacks & Queues (51-60)
    # ==========================================
    (51, "Valid Parentheses", """
    import flowlib;
    dfn is_valid_parens(str s) -> bool {
        list stack = [];
        for i in (0; i < len_(s); i = i + 1) {
            str c = s[i];
            if c == "(" or c == "{" or c == "[" {
                append_(stack, c);
            } else {
                if len_(stack) == 0 { return false; }
                str top = stack[len_(stack) - 1];
                pop_(stack);
                if c == ")" and top != "(" { return false; }
                if c == "}" and top != "{" { return false; }
                if c == "]" and top != "[" { return false; }
            }
        }
        return len_(stack) == 0;
    }
    say(is_valid_parens("()[]{}"));
    say(is_valid_parens("(]"));
    """, "true\nfalse"),

    (52, "Evaluate Reverse Polish Notation", """
    import flowlib;
    dfn eval_rpn(list tokens) -> int {
        list stack = [];
        for tok in tokens {
            str t = str_(tok);
            if t == "+" {
                int b = stack[len_(stack) - 1];
                pop_(stack);
                int a = stack[len_(stack) - 1];
                pop_(stack);
                append_(stack, a + b);
            } elif t == "-" {
                int b = stack[len_(stack) - 1];
                pop_(stack);
                int a = stack[len_(stack) - 1];
                pop_(stack);
                append_(stack, a - b);
            } elif t == "*" {
                int b = stack[len_(stack) - 1];
                pop_(stack);
                int a = stack[len_(stack) - 1];
                pop_(stack);
                append_(stack, a * b);
            } elif t == "/" {
                int b = stack[len_(stack) - 1];
                pop_(stack);
                int a = stack[len_(stack) - 1];
                pop_(stack);
                append_(stack, a // b);
            } else {
                append_(stack, int_(t));
            }
        }
        return stack[0];
    }
    say(eval_rpn(["2", "1", "+", "3", "*"]));
    say(eval_rpn(["4", "13", "5", "/", "+"]));
    """, "9\n6"),

    (53, "Next Greater Element I", """
    import flowlib;
    dfn next_greater_element(list nums1, list nums2) -> list {
        dict nge = << >>;
        list stack = [];
        for x in nums2 {
            int v = int_(x);
            while len_(stack) > 0 and stack[len_(stack) - 1] < v {
                nge[stack[len_(stack) - 1]] = v;
                pop_(stack);
            }
            append_(stack, v);
        }
        list res = [];
        for x in nums1 {
            int v = int_(x);
            append_(res, get_(nge, v, -1));
        }
        return res;
    }
    say(next_greater_element([4, 1, 2], [1, 3, 4, 2]));
    """, "[-1, 3, -1]"),

    (54, "Daily Temperatures", """
    import flowlib;
    dfn daily_temperatures(list temps) -> list {
        int n = len_(temps);
        list res = [];
        for i in (0; i < n; i = i + 1) { append_(res, 0); }
        list stack = [];
        for i in (0; i < n; i = i + 1) {
            while len_(stack) > 0 and temps[i] > temps[stack[len_(stack) - 1]] {
                int prev_idx = stack[len_(stack) - 1];
                pop_(stack);
                res[prev_idx] = i - prev_idx;
            }
            append_(stack, i);
        }
        return res;
    }
    say(daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]));
    """, "[1, 1, 4, 2, 1, 1, 0, 0]"),

    (55, "Queue via Array (Enqueue, Dequeue, Peek)", """
    import flowlib;
    dfn queue_demo() -> list {
        list q = [];
        append_(q, 10);
        append_(q, 20);
        append_(q, 30);
        list out = [];
        append_(out, q[0]);
        pop_(q, 0);
        append_(out, q[0]);
        pop_(q, 0);
        append_(out, q[0]);
        return out;
    }
    say(queue_demo());
    """, "[10, 20, 30]"),

    (56, "Asteroid Collision", """
    import flowlib;
    dfn asteroid_collision(list asteroids) -> list {
        list stack = [];
        for ast in asteroids {
            int a = int_(ast);
            mut bool alive = true;
            while alive and a < 0 and len_(stack) > 0 and stack[len_(stack) - 1] > 0 {
                int top = stack[len_(stack) - 1];
                if top < -a {
                    pop_(stack);
                } elif top == -a {
                    pop_(stack);
                    alive = false;
                } else {
                    alive = false;
                }
            }
            if alive {
                append_(stack, a);
            }
        }
        return stack;
    }
    say(asteroid_collision([5, 10, -5]));
    say(asteroid_collision([8, -8]));
    say(asteroid_collision([10, 2, -5]));
    """, "[5, 10]\n[]\n[10]"),

    (57, "Simplify Path Simulation", """
    import flowlib;
    dfn simplify_path_demo(list parts) -> str {
        list stack = [];
        for p in parts {
            str part = str_(p);
            if part == "" or part == "." {
                # skip
            } elif part == ".." {
                if len_(stack) > 0 {
                    pop_(stack);
                }
            } else {
                append_(stack, part);
            }
        }
        mut str res = "";
        for seg in stack {
            res = res + "/" + str_(seg);
        }
        if res == "" { return "/"; }
        return res;
    }
    say(simplify_path_demo(["home", "user", "Documents", "..", "Pictures"]));
    say(simplify_path_demo(["a", "..", "b", "c", ".."]));
    """, "/home/user/Pictures\n/b"),

    (58, "Min Stack Simulation", """
    import flowlib;
    dfn min_stack_demo() -> list {
        list stack = [];
        list min_stk = [];
        # push 5
        append_(stack, 5);
        append_(min_stk, 5);
        # push 3
        append_(stack, 3);
        append_(min_stk, 3);
        # push 7
        append_(stack, 7);
        append_(min_stk, 3);
        list res = [];
        append_(res, min_stk[len_(min_stk) - 1]); # min is 3
        # pop 7
        pop_(stack);
        pop_(min_stk);
        # pop 3
        pop_(stack);
        pop_(min_stk);
        append_(res, min_stk[len_(min_stk) - 1]); # min is 5
        return res;
    }
    say(min_stack_demo());
    """, "[3, 5]"),

    (59, "Circular Buffer (Array-based Ring Buffer)", """
    dfn ring_buffer_demo() -> list {
        list buf = [0, 0, 0];
        mut int head = 0;
        mut int count = 0;
        int cap = 3;
        # enqueue 1, 2, 3
        buf[(head + count) % cap] = 10; count = count + 1;
        buf[(head + count) % cap] = 20; count = count + 1;
        buf[(head + count) % cap] = 30; count = count + 1;
        # dequeue 1
        list out = [];
        append_(out, buf[head]); head = (head + 1) % cap; count = count - 1;
        # enqueue 40
        buf[(head + count) % cap] = 40; count = count + 1;
        # dequeue rest
        while count > 0 {
            append_(out, buf[head]);
            head = (head + 1) % cap;
            count = count - 1;
        }
        return out;
    }
    say(ring_buffer_demo());
    """, "[10, 20, 30, 40]"),

    (60, "Remove All Adjacent Duplicates in String", """
    import flowlib;
    dfn remove_adjacent_duplicates(str s) -> str {
        list stack = [];
        for i in (0; i < len_(s); i = i + 1) {
            str c = s[i];
            if len_(stack) > 0 and stack[len_(stack) - 1] == c {
                pop_(stack);
            } else {
                append_(stack, c);
            }
        }
        mut str res = "";
        for c in stack { res = res + str_(c); }
        return res;
    }
    say(remove_adjacent_duplicates("abbaca"));
    """, "ca"),

    # ==========================================
    # Category 7: Recursion & Backtracking (61-70)
    # ==========================================
    (61, "Fibonacci (Recursive with Memoization)", """
    import flowlib;
    dfn fib_memo(int n, dict memo) -> int {
        if n <= 1 { return n; }
        int cached = get_(memo, n, -1);
        if cached != -1 { return cached; }
        int res = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
        memo[n] = res;
        return res;
    }
    dict m = << >>;
    say(fib_memo(10, m));
    say(fib_memo(15, m));
    """, "55\n610"),

    (62, "Power Function Pow(x, n) via Exponentiation by Squaring", """
    dfn quick_pow(int base, int exp) -> int {
        if exp == 0 { return 1; }
        if exp % 2 == 0 {
            int half = quick_pow(base, exp // 2);
            return half * half;
        } else {
            return base * quick_pow(base, exp - 1);
        }
    }
    say(quick_pow(2, 10));
    say(quick_pow(3, 5));
    """, "1024\n243"),

    (63, "Tower of Hanoi Move Counter", """
    dfn hanoi_moves(int n) -> int {
        if n == 1 { return 1; }
        return 2 * hanoi_moves(n - 1) + 1;
    }
    say(hanoi_moves(3));
    say(hanoi_moves(4));
    """, "7\n15"),

    (64, "Subset Generation (Bitmasking count)", """
    dfn count_subsets_sum(list nums, int target, int idx, int cur_sum) -> int {
        if idx == len_(nums) {
            if cur_sum == target { return 1; }
            return 0;
        }
        int include_cnt = count_subsets_sum(nums, target, idx + 1, cur_sum + nums[idx]);
        int exclude_cnt = count_subsets_sum(nums, target, idx + 1, cur_sum);
        return include_cnt + exclude_cnt;
    }
    say(count_subsets_sum([1, 2, 3], 3, 0, 0));
    """, "2"),

    (65, "Permutations Count", """
    dfn perm_count(int n, int r) -> int {
        if r == 0 { return 1; }
        return n * perm_count(n - 1, r - 1);
    }
    say(perm_count(5, 3));
    """, "60"),

    (66, "Combinations Count nCr", """
    dfn n_cr(int n, int r) -> int {
        if r == 0 or r == n { return 1; }
        return n_cr(n - 1, r - 1) + n_cr(n - 1, r);
    }
    say(n_cr(5, 2));
    say(n_cr(6, 3));
    """, "10\n20"),

    (67, "Count Binary Trees with N Nodes (Catalan Numbers)", """
    dfn catalan(int n) -> int {
        if n <= 1 { return 1; }
        mut int res = 0;
        for i in (0; i < n; i = i + 1) {
            res = res + catalan(int_(i)) * catalan(n - 1 - int_(i));
        }
        return res;
    }
    say(catalan(3));
    say(catalan(4));
    """, "5\n14"),

    (68, "N-Queens Safe Placement Counter (4-Queens)", """
    dfn is_safe(list board, int row, int col) -> bool {
        for i in (0; i < row; i = i + 1) {
            int placed_col = board[i];
            if placed_col == col { return false; }
            int row_diff = row - int_(i);
            mut int col_diff = col - placed_col;
            if col_diff < 0 { col_diff = -col_diff; }
            if row_diff == col_diff { return false; }
        }
        return true;
    }
    dfn solve_n_queens(list board, int row, int n) -> int {
        if row == n { return 1; }
        mut int total = 0;
        for col in (0; col < n; col = col + 1) {
            if is_safe(board, row, int_(col)) {
                board[row] = int_(col);
                total = total + solve_n_queens(board, row + 1, n);
            }
        }
        return total;
    }
    say(solve_n_queens([0, 0, 0, 0], 0, 4));
    """, "2"),

    (69, "Josephus Problem", """
    dfn josephus(int n, int k) -> int {
        if n == 1 { return 0; }
        return (josephus(n - 1, k) + k) % n;
    }
    say(josephus(5, 2) + 1);
    say(josephus(7, 3) + 1);
    """, "3\n4"),

    (70, "Letter Combinations Count", """
    dfn letter_combinations_count(str digits) -> int {
        if len_(digits) == 0 { return 0; }
        mut int total = 1;
        for i in (0; i < len_(digits); i = i + 1) {
            str d = digits[i];
            if d == "7" or d == "9" {
                total = total * 4;
            } else {
                total = total * 3;
            }
        }
        return total;
    }
    say(letter_combinations_count("23"));
    say(letter_combinations_count("279"));
    """, "9\n48"),

    # ==========================================
    # Category 8: Dynamic Programming 1D / 2D (71-80)
    # ==========================================
    (71, "Climbing Stairs (DP 1D)", """
    dfn climb_stairs(int n) -> int {
        if n <= 2 { return n; }
        mut int a = 1;
        mut int b = 2;
        for i in (3; i <= n; i = i + 1) {
            int c = a + b;
            a = b;
            b = c;
        }
        return b;
    }
    say(climb_stairs(4));
    say(climb_stairs(5));
    """, "5\n8"),

    (72, "House Robber", """
    dfn rob(list nums) -> int {
        int n = len_(nums);
        if n == 0 { return 0; }
        if n == 1 { return nums[0]; }
        mut int prev2 = nums[0];
        mut int prev1 = nums[0];
        if nums[1] > prev1 { prev1 = nums[1]; }
        for i in (2; i < n; i = i + 1) {
            mut int cur = prev2 + nums[i];
            if prev1 > cur { cur = prev1; }
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }
    say(rob([1, 2, 3, 1]));
    say(rob([2, 7, 9, 3, 1]));
    """, "4\n12"),

    (73, "Coin Change (DP Minimum Coins)", """
    dfn coin_change(list coins, int amount) -> int {
        list dp = [];
        for i in (0; i <= amount; i = i + 1) { append_(dp, 2147483647); }
        dp[0] = 0;
        for a in (1; a <= amount; a = a + 1) {
            for c in coins {
                int coin_val = int_(c);
                if a - coin_val >= 0 and dp[a - coin_val] != 2147483647 {
                    int cand = dp[a - coin_val] + 1;
                    if cand < dp[a] { dp[a] = cand; }
                }
            }
        }
        if dp[amount] == 2147483647 { return -1; }
        return dp[amount];
    }
    say(coin_change([1, 2, 5], 11));
    say(coin_change([2], 3));
    """, "3\n-1"),

    (74, "Longest Increasing Subsequence Length (DP)", """
    dfn lis(list nums) -> int {
        int n = len_(nums);
        if n == 0 { return 0; }
        list dp = [];
        for i in (0; i < n; i = i + 1) { append_(dp, 1); }
        mut int max_lis = 1;
        for i in (1; i < n; i = i + 1) {
            for j in (0; j < i; j = j + 1) {
                if nums[j] < nums[i] and dp[j] + 1 > dp[i] {
                    dp[i] = dp[j] + 1;
                }
            }
            if dp[i] > max_lis { max_lis = dp[i]; }
        }
        return max_lis;
    }
    say(lis([10, 9, 2, 5, 3, 7, 101, 18]));
    """, "4"),

    (75, "Unique Paths in Grid (DP 2D)", """
    dfn unique_paths(int m, int n) -> int {
        list row = [];
        for j in (0; j < n; j = j + 1) { append_(row, 1); }
        for i in (1; i < m; i = i + 1) {
            for j in (1; j < n; j = j + 1) {
                row[j] = row[j] + row[j - 1];
            }
        }
        return row[n - 1];
    }
    say(unique_paths(3, 7));
    say(unique_paths(3, 2));
    """, "28\n3"),

    (76, "0/1 Knapsack Problem (DP)", """
    dfn knapsack(list weights, list values, int W) -> int {
        int n = len_(weights);
        list dp = [];
        for w in (0; w <= W; w = w + 1) { append_(dp, 0); }
        for i in (0; i < n; i = i + 1) {
            int wt = weights[i];
            int val = values[i];
            mut int w = W;
            while w >= wt {
                if dp[w - wt] + val > dp[w] {
                    dp[w] = dp[w - wt] + val;
                }
                w = w - 1;
            }
        }
        return dp[W];
    }
    say(knapsack([1, 3, 4, 5], [1, 4, 5, 7], 7));
    """, "9"),

    (77, "Longest Common Subsequence Length (DP)", """
    dfn lcs(str s1, str s2) -> int {
        int m = len_(s1);
        int n = len_(s2);
        list dp = [];
        for i in (0; i <= m; i = i + 1) {
            list row = [];
            for j in (0; j <= n; j = j + 1) { append_(row, 0); }
            append_(dp, row);
        }
        for i in (1; i <= m; i = i + 1) {
            for j in (1; j <= n; j = j + 1) {
                if s1[i - 1] == s2[j - 1] {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    int c1 = dp[i - 1][j];
                    int c2 = dp[i][j - 1];
                    if c1 > c2 { dp[i][j] = c1; }
                    else { dp[i][j] = c2; }
                }
            }
        }
        return dp[m][n];
    }
    say(lcs("abcde", "ace"));
    say(lcs("abc", "def"));
    """, "3\n0"),

    (78, "Min Cost Climbing Stairs", """
    dfn min_cost_climbing(list cost) -> int {
        int n = len_(cost);
        mut int prev2 = cost[0];
        mut int prev1 = cost[1];
        for i in (2; i < n; i = i + 1) {
            mut int min_prev = prev2;
            if prev1 < min_prev { min_prev = prev1; }
            int cur = cost[i] + min_prev;
            prev2 = prev1;
            prev1 = cur;
        }
        if prev1 < prev2 { return prev1; }
        return prev2;
    }
    say(min_cost_climbing([10, 15, 20]));
    say(min_cost_climbing([1, 100, 1, 1, 1, 100, 1, 1, 100, 1]));
    """, "15\n6"),

    (79, "Jump Game I (Greedy)", """
    dfn can_jump(list nums) -> bool {
        mut int max_reach = 0;
        int n = len_(nums);
        for i in (0; i < n; i = i + 1) {
            if i > max_reach { return false; }
            if i + nums[i] > max_reach {
                max_reach = i + nums[i];
            }
        }
        return max_reach >= n - 1;
    }
    say(can_jump([2, 3, 1, 1, 4]));
    say(can_jump([3, 2, 1, 0, 4]));
    """, "true\nfalse"),

    (80, "Best Time to Buy and Sell Stock (Single Transaction)", """
    dfn max_profit(list prices) -> int {
        if len_(prices) == 0 { return 0; }
        mut int min_price = prices[0];
        mut int max_prof = 0;
        for p in prices {
            int v = int_(p);
            if v < min_price { min_price = v; }
            int prof = v - min_price;
            if prof > max_prof { max_prof = prof; }
        }
        return max_prof;
    }
    say(max_profit([7, 1, 5, 3, 6, 4]));
    say(max_profit([7, 6, 4, 3, 1]));
    """, "5\n0"),

    # ==========================================
    # Category 9: 2D Matrices & Grid Traversal (81-90)
    # ==========================================
    (81, "Transpose Matrix 2D", """
    dfn transpose(list matrix) -> list {
        int r = len_(matrix);
        int c = len_(matrix[0]);
        list res = [];
        for j in (0; j < c; j = j + 1) {
            list row = [];
            for i in (0; i < r; i = i + 1) {
                append_(row, matrix[i][j]);
            }
            append_(res, row);
        }
        return res;
    }
    say(transpose([[1, 2, 3], [4, 5, 6]]));
    """, "[[1, 4], [2, 5], [3, 6]]"),

    (82, "Rotate Matrix 90 Degrees Clockwise", """
    dfn rotate_matrix(list matrix) -> list {
        int n = len_(matrix);
        # transpose
        for i in (0; i < n; i = i + 1) {
            for j in (i + 1; j < n; j = j + 1) {
                int tmp = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = tmp;
            }
        }
        # reverse rows
        for i in (0; i < n; i = i + 1) {
            mut int l = 0;
            mut int r = n - 1;
            while l < r {
                int tmp = matrix[i][l];
                matrix[i][l] = matrix[i][r];
                matrix[i][r] = tmp;
                l = l + 1;
                r = r - 1;
            }
        }
        return matrix;
    }
    say(rotate_matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]]));
    """, "[[7, 4, 1], [8, 5, 2], [9, 6, 3]]"),

    (83, "Matrix Multiplication", """
    dfn mat_mul(list A, list B) -> list {
        int r1 = len_(A);
        int c1 = len_(A[0]);
        int c2 = len_(B[0]);
        list C = [];
        for i in (0; i < r1; i = i + 1) {
            list row = [];
            for j in (0; j < c2; j = j + 1) {
                mut int s = 0;
                for k in (0; k < c1; k = k + 1) {
                    s = s + A[i][k] * B[k][j];
                }
                append_(row, s);
            }
            append_(C, row);
        }
        return C;
    }
    say(mat_mul([[1, 2], [3, 4]], [[5, 6], [7, 8]]));
    """, "[[19, 22], [43, 50]]"),

    (84, "Pascal's Triangle Row Generator", """
    dfn get_pascal_row(int rowIndex) -> list {
        list row = [1];
        for i in (1; i <= rowIndex; i = i + 1) {
            list next_row = [1];
            for j in (1; j < i; j = j + 1) {
                append_(next_row, row[j - 1] + row[j]);
            }
            append_(next_row, 1);
            row = next_row;
        }
        return row;
    }
    say(get_pascal_row(4));
    """, "[1, 4, 6, 4, 1]"),

    (85, "Set Matrix Zeroes Check", """
    dfn zero_matrix(list mat) -> list {
        int m = len_(mat);
        int n = len_(mat[0]);
        list zero_rows = [];
        list zero_cols = [];
        for i in (0; i < m; i = i + 1) { append_(zero_rows, false); }
        for j in (0; j < n; j = j + 1) { append_(zero_cols, false); }
        for i in (0; i < m; i = i + 1) {
            for j in (0; j < n; j = j + 1) {
                if mat[i][j] == 0 {
                    zero_rows[i] = true;
                    zero_cols[j] = true;
                }
            }
        }
        for i in (0; i < m; i = i + 1) {
            for j in (0; j < n; j = j + 1) {
                if zero_rows[i] or zero_cols[j] {
                    mat[i][j] = 0;
                }
            }
        }
        return mat;
    }
    say(zero_matrix([[1, 1, 1], [1, 0, 1], [1, 1, 1]]));
    """, "[[1, 0, 1], [0, 0, 0], [1, 0, 1]]"),

    (86, "Number of Islands Simulation (Connected Components Count)", """
    import flowlib;
    dfn count_components_grid(list grid) -> int {
        int r = len_(grid);
        int c = len_(grid[0]);
        mut int count = 0;
        for i in (0; i < r; i = i + 1) {
            for j in (0; j < c; j = j + 1) {
                if grid[i][j] == 1 {
                    count = count + 1;
                    list stack = [[int_(i), int_(j)]];
                    grid[i][j] = 0;
                    while len_(stack) > 0 {
                        list cur = listb_(stack[len_(stack) - 1]);
                        pop_(stack);
                        int cr = cur[0];
                        int cc = cur[1];
                        if cr + 1 < r and grid[cr + 1][cc] == 1 {
                            grid[cr + 1][cc] = 0;
                            append_(stack, [cr + 1, cc]);
                        }
                        if cr - 1 >= 0 and grid[cr - 1][cc] == 1 {
                            grid[cr - 1][cc] = 0;
                            append_(stack, [cr - 1, cc]);
                        }
                        if cc + 1 < c and grid[cr][cc + 1] == 1 {
                            grid[cr][cc + 1] = 0;
                            append_(stack, [cr, cc + 1]);
                        }
                        if cc - 1 >= 0 and grid[cr][cc - 1] == 1 {
                            grid[cr][cc - 1] = 0;
                            append_(stack, [cr, cc - 1]);
                        }
                    }
                }
            }
        }
        return count;
    }
    say(count_components_grid([[1, 1, 0], [0, 1, 0], [0, 0, 1]]));
    """, "2"),

    (87, "Flood Fill Simulation", """
    dfn flood_fill_sample(list image, int sr, int sc, int newColor) -> list {
        int orig = image[sr][sc];
        if orig == newColor { return image; }
        image[sr][sc] = newColor;
        int r = len_(image);
        int c = len_(image[0]);
        if sr - 1 >= 0 and image[sr - 1][sc] == orig { image[sr - 1][sc] = newColor; }
        if sr + 1 < r and image[sr + 1][sc] == orig { image[sr + 1][sc] = newColor; }
        if sc - 1 >= 0 and image[sr][sc - 1] == orig { image[sr][sc - 1] = newColor; }
        if sc + 1 < c and image[sr][sc + 1] == orig { image[sr][sc + 1] = newColor; }
        return image;
    }
    say(flood_fill_sample([[1, 1, 1], [1, 1, 0], [1, 0, 1]], 1, 1, 2));
    """, "[[1, 2, 1], [2, 2, 0], [1, 0, 1]]"),

    (88, "Spiral Matrix (First Layer Unroll)", """
    dfn spiral_layer(list mat) -> list {
        list res = [];
        int top = 0;
        int bottom = len_(mat) - 1;
        int left = 0;
        int right = len_(mat[0]) - 1;
        # top row
        for j in (left; j <= right; j = j + 1) { append_(res, mat[top][j]); }
        # right col
        for i in (top + 1; i <= bottom; i = i + 1) { append_(res, mat[i][right]); }
        # bottom row
        mut int j = right - 1;
        while j >= left { append_(res, mat[bottom][j]); j = j - 1; }
        # left col
        mut int i = bottom - 1;
        while i > top { append_(res, mat[i][left]); i = i - 1; }
        return res;
    }
    say(spiral_layer([[1, 2, 3], [4, 5, 6], [7, 8, 9]]));
    """, "[1, 2, 3, 6, 9, 8, 7, 4]"),

    (89, "Diagonal Sum of Square Matrix", """
    dfn diagonal_sum(list mat) -> int {
        int n = len_(mat);
        mut int total = 0;
        for i in (0; i < n; i = i + 1) {
            total = total + mat[i][i];
            int j = n - 1 - i;
            if j != i {
                total = total + mat[i][j];
            }
        }
        return total;
    }
    say(diagonal_sum([[1, 2, 3], [4, 5, 6], [7, 8, 9]]));
    """, "25"),

    (90, "Minimum Path Sum (2x2 Grid)", """
    dfn min_path_sum(list grid) -> int {
        int m = len_(grid);
        int n = len_(grid[0]);
        for i in (0; i < m; i = i + 1) {
            for j in (0; j < n; j = j + 1) {
                if i == 0 and j == 0 {
                    # keep
                } elif i == 0 {
                    grid[i][j] = grid[i][j] + grid[i][j - 1];
                } elif j == 0 {
                    grid[i][j] = grid[i][j] + grid[i - 1][j];
                } else {
                    int c1 = grid[i - 1][j];
                    int c2 = grid[i][j - 1];
                    if c1 < c2 { grid[i][j] = grid[i][j] + c1; }
                    else { grid[i][j] = grid[i][j] + c2; }
                }
            }
        }
        return grid[m - 1][n - 1];
    }
    say(min_path_sum([[1, 3, 1], [1, 5, 1], [4, 2, 1]]));
    """, "7"),

    # ==========================================
    # Category 10: Systems & Infrastructure Simulations (91-100)
    # ==========================================
    (91, "LRU Cache Simulation (Array & Dict Based)", """
    import flowlib;
    dfn lru_simulation() -> list {
        int capacity = 2;
        dict cache = << >>;
        list order = [];
        list out = [];

        # put 1:100
        cache[1] = 100;
        append_(order, 1);

        # put 2:200
        cache[2] = 200;
        append_(order, 2);

        # get 1 -> returns 100, make 1 most recent
        append_(out, cache[1]);
        # move 1 to end of order
        pop_(order, 0);
        append_(order, 1);

        # put 3:300 -> evicts 2 (oldest)
        int lru_key = order[0];
        pop_(order, 0);
        pop_(cache, lru_key);
        cache[3] = 300;
        append_(order, 3);

        # get 2 -> not found (-1)
        append_(out, get_(cache, 2, -1));
        # get 3 -> 300
        append_(out, get_(cache, 3, -1));

        return out;
    }
    say(lru_simulation());
    """, "[100, -1, 300]"),

    (92, "Disjoint Set Union (DSU / Union-Find)", """
    dfn dsu_simulation() -> list {
        list parent = [0, 1, 2, 3, 4];
        list results = [];

        # union 0, 1
        int rx0 = 0; while parent[rx0] != rx0 { rx0 = parent[rx0]; }
        int ry0 = 1; while parent[ry0] != ry0 { ry0 = parent[ry0]; }
        if rx0 != ry0 {
            parent[ry0] = rx0;
            append_(results, true);
        } else {
            append_(results, false);
        }

        # union 1, 2
        mut int rx1 = 1; while parent[rx1] != rx1 { rx1 = parent[rx1]; }
        int ry1 = 2; while parent[ry1] != ry1 { ry1 = parent[ry1]; }
        if rx1 != ry1 {
            parent[ry1] = rx1;
            append_(results, true);
        } else {
            append_(results, false);
        }

        # union 0, 2 (already connected)
        int rx2 = 0; while parent[rx2] != rx2 { rx2 = parent[rx2]; }
        mut int ry2 = 2; while parent[ry2] != ry2 { ry2 = parent[ry2]; }
        if rx2 != ry2 {
            parent[ry2] = rx2;
            append_(results, true);
        } else {
            append_(results, false);
        }

        mut int r2 = 2; while parent[r2] != r2 { r2 = parent[r2]; }
        int r0 = 0; while parent[r0] != r0 { r0 = parent[r0]; }
        append_(results, r2 == r0);

        return results;
    }
    say(dsu_simulation());
    """, "[true, true, false, true]"),

    (93, "Bitmask State Representation (Flag Set)", """
    # FlowLang integer simulation of bitwise state flags via powers of 2
    dfn has_flag(int state, int flag_val) -> bool {
        return (state // flag_val) % 2 == 1;
    }
    dfn set_flag(int state, int flag_val) -> int {
        if has_flag(state, flag_val) { return state; }
        return state + flag_val;
    }
    dfn clear_flag(int state, int flag_val) -> int {
        if has_flag(state, flag_val) { return state - flag_val; }
        return state;
    }
    int READ_FLAG = 1;
    int WRITE_FLAG = 2;
    int EXEC_FLAG = 4;
    mut int state = 0;
    state = set_flag(state, READ_FLAG);
    state = set_flag(state, EXEC_FLAG);
    say(has_flag(state, READ_FLAG));
    say(has_flag(state, WRITE_FLAG));
    say(has_flag(state, EXEC_FLAG));
    state = clear_flag(state, READ_FLAG);
    say(has_flag(state, READ_FLAG));
    """, "true\nfalse\ntrue\nfalse"),

    (94, "Min-Heap Insert and Extract-Min Simulation", """
    import flowlib;
    dfn heap_demo() -> list {
        list heap = [];
        list out = [];
        list to_push = [30, 10, 20, 5];
        for val in to_push {
            int v = int_(val);
            append_(heap, v);
            mut int idx = len_(heap) - 1;
            while idx > 0 {
                int p = (idx - 1) // 2;
                if heap[idx] < heap[p] {
                    int tmp = heap[idx];
                    heap[idx] = heap[p];
                    heap[p] = tmp;
                    idx = p;
                } else {
                    idx = 0;
                }
            }
        }
        while len_(heap) > 0 {
            int min_val = heap[0];
            heap[0] = heap[len_(heap) - 1];
            pop_(heap);
            mut int idx = 0;
            int n = len_(heap);
            while 2 * idx + 1 < n {
                int left = 2 * idx + 1;
                int right = 2 * idx + 2;
                int smallest = left;
                if right < n and heap[right] < heap[left] {
                    smallest = right;
                }
                if heap[smallest] < heap[idx] {
                    int tmp = heap[idx];
                    heap[idx] = heap[smallest];
                    heap[smallest] = tmp;
                    idx = smallest;
                } else {
                    idx = n;
                }
            }
            append_(out, min_val);
        }
        return out;
    }
    say(heap_demo());
    """, "[5, 10, 20, 30]"),

    (95, "Adjacency List Graph BFS Reachability", """
    import flowlib;
    dfn bfs_reachable(dict graph, int start_node, int target_node) -> bool {
        list q = [start_node];
        dict visited = << start_node : true >>;
        while len_(q) > 0 {
            int cur = q[0];
            pop_(q, 0);
            if cur == target_node { return true; }
            list neighbors = get_(graph, cur, []);
            for neighbor in neighbors {
                int n_val = int_(neighbor);
                bool has_visited = get_(visited, n_val, false);
                if not has_visited {
                    visited[n_val] = true;
                    append_(q, n_val);
                }
            }
        }
        return false;
    }
    dict g = <<
        0 : [1, 2],
        1 : [2],
        2 : [0, 3],
        3 : [3]
    >>;
    say(bfs_reachable(g, 2, 3));
    say(bfs_reachable(g, 3, 1));
    """, "true\nfalse"),

    (96, "Topological Sort Degree Check (DAG Simulation)", """
    import flowlib;
    dfn can_finish_tasks(int numCourses, list prerequisites) -> bool {
        dict in_degree = << >>;
        dict adj = << >>;
        for i in (0; i < numCourses; i = i + 1) {
            in_degree[i] = 0;
            adj[i] = [];
        }
        for pair in prerequisites {
            list p = listb_(pair);
            int dest = p[0];
            int src = p[1];
            append_(adj[src], dest);
            in_degree[dest] = in_degree[dest] + 1;
        }
        list q = [];
        for i in (0; i < numCourses; i = i + 1) {
            if in_degree[i] == 0 {
                append_(q, i);
            }
        }
        mut int visited_count = 0;
        while len_(q) > 0 {
            int node = q[0];
            pop_(q, 0);
            visited_count = visited_count + 1;
            for nbr in adj[node] {
                int n_val = int_(nbr);
                in_degree[n_val] = in_degree[n_val] - 1;
                if in_degree[n_val] == 0 {
                    append_(q, n_val);
                }
            }
        }
        return visited_count == numCourses;
    }
    say(can_finish_tasks(2, [[1, 0]]));
    say(can_finish_tasks(2, [[1, 0], [0, 1]]));
    """, "true\nfalse"),

    (97, "Dijkstra Shortest Path Simulation", """
    import flowlib;
    dfn dijkstra_min(int n, dict edges, int src) -> list {
        list dist = [];
        list visited = [];
        for i in (0; i < n; i = i + 1) {
            append_(dist, 2147483647);
            append_(visited, false);
        }
        dist[src] = 0;
        for count in (0; count < n; count = count + 1) {
            mut int min_d = 2147483647;
            mut int u = -1;
            for i in (0; i < n; i = i + 1) {
                if not visited[i] and dist[i] < min_d {
                    min_d = dist[i];
                    u = int_(i);
                }
            }
            if u != -1 {
                visited[u] = true;
                list nbrs = get_(edges, u, []);
                for edge in nbrs {
                    list ed = listb_(edge);
                    int v = ed[0];
                    int weight = ed[1];
                    if not visited[v] and dist[u] + weight < dist[v] {
                        dist[v] = dist[u] + weight;
                    }
                }
            }
        }
        return dist;
    }
    dict graph = <<
        0 : [[1, 4], [2, 1]],
        1 : [[3, 1]],
        2 : [[1, 2], [3, 5]],
        3 : []
    >>;
    say(dijkstra_min(4, graph, 0));
    """, "[0, 3, 1, 4]"),

    (98, "Trie (Prefix Tree) Word Insertion & Lookup", """
    import flowlib;
    dfn trie_demo() -> list {
        # Trie prefix and exact-word dictionary simulation
        dict prefixes = << >>;
        dict words = << >>;

        # insert "app"
        str word = "app";
        words[word] = true;
        mut str pref = "";
        for i in (0; i < len_(word); i = i + 1) {
            pref = pref + word[i];
            prefixes[pref] = true;
        }

        # search "app" -> exact match
        bool app_found = get_(words, "app", false);

        # search prefix "ap" -> prefix match
        bool ap_prefix = get_(prefixes, "ap", false);

        # search "apple" -> false
        bool apple_found = get_(words, "apple", false);

        return [app_found, ap_prefix, apple_found];
    }
    say(trie_demo());
    """, "[true, true, false]"),

    (99, "Free List Memory Allocator Simulation", """
    dfn allocator_demo() -> list {
        list pool = [0, 0, 0, 0];
        list addresses = [];

        # allocate 64
        mut int a1 = -1;
        for i in (0; i < len_(pool); i = i + 1) {
            if a1 == -1 and pool[i] == 0 { pool[i] = 64; a1 = int_(i); }
        }
        append_(addresses, a1);

        # allocate 128
        mut int a2 = -1;
        for i in (0; i < len_(pool); i = i + 1) {
            if a2 == -1 and pool[i] == 0 { pool[i] = 128; a2 = int_(i); }
        }
        append_(addresses, a2);

        # free a1 (block 0)
        pool[a1] = 0;

        # allocate 256 (reuses block 0)
        mut int a3 = -1;
        for i in (0; i < len_(pool); i = i + 1) {
            if a3 == -1 and pool[i] == 0 { pool[i] = 256; a3 = int_(i); }
        }
        append_(addresses, a3);

        return addresses;
    }
    say(allocator_demo());
    """, "[0, 1, 0]"),

    (100, "Huffman Frequency Tree Weights (Greedy Pairing)", """
    import flowlib;
    dfn huffman_tree_cost(list freqs) -> int {
        asort_(freqs);
        mut int total_cost = 0;
        while len_(freqs) > 1 {
            int a = freqs[0];
            pop_(freqs, 0);
            int b = freqs[0];
            pop_(freqs, 0);
            int combined = a + b;
            total_cost = total_cost + combined;
            append_(freqs, combined);
            asort_(freqs);
        }
        return total_cost;
    }
    say(huffman_tree_cost([5, 9, 12, 13, 16, 45]));
    """, "224")
]

import unittest


class TestDSA100Benchmark(unittest.TestCase):
    def test_all_100_problems(self):
        failures = []
        for pid, name, code, expected in problems:
            res = execute(code)
            if res.formatted_error:
                failures.append(f"[{pid}] {name}: {res.formatted_error}")
            elif res.output.strip() != expected.strip():
                failures.append(f"[{pid}] {name}: Got {res.output.strip()!r} Expected {expected.strip()!r}")
        self.assertEqual(failures, [], f"DSA failures: {failures}")


def run_all():
    passed = 0
    failed = 0
    failures = []
    for pid, name, code, expected in problems:
        try:
            res = execute(code)
            if res.formatted_error:
                failed += 1
                failures.append(f"FAILED [{pid}] {name}: RUNTIME/PARSE ERROR:\n{res.formatted_error}")
            else:
                actual = res.output.strip()
                if actual == expected.strip():
                    passed += 1
                else:
                    failed += 1
                    failures.append(f"FAILED [{pid}] {name}: MISMATCH:\nActual: {actual}\nExpected: {expected.strip()}")
        except Exception as e:
            failed += 1
            failures.append(f"FAILED [{pid}] {name}: EXCEPTION: {e}")

    print(f"Total: {len(problems)} | Passed: {passed} | Failed: {failed}")
    for f in failures:
        print(f)

if __name__ == "__main__":
    unittest.main()
