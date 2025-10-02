# Bugzilla API

The purpose of this document is to highlight key aspects of the Bugzilla API related to the fields, filters, and queries that are most relevant when fetching data and generating metrics for bug tracking and release analysis.

# Bugs per Release

To determine the different metrics needed, the bugs are fetched using the QA Witheboard field. That is the primary filter, then depending on the value of other fields, the data is generated.

## Filter

1. **QA Whiteboard field**  
   - The QA Whiteboard is used to identify bugs that were open in a given release cycle.  
   - Example values:  
     ```
     [qa-found-in-c141] [qa-found-in-b141]
     ```  
   - These values indicate that the bug was open in release **141**, either in Nightly (c) or Beta (b).

## Fields Tracked

1. **Keywords**
   - Regression information is added here
2. **Status**
   - So that bugs can be grouped in Open, Resolved
3. **Resoultion**
   - Bugzilla uses Resolution also to give more information about the final Status. For example, Resolved as Duplicated.
4. **Created At**
   - When the bug was logged in
5. **Closed**
   - When the bug was closed
6. **Severity**
   - Indicates the impact of the bug
7. **Whiteboard**
   - To have information about different type of bugs, like: papercuts.

# Bugs Fixed Tracking by Release Date

 Logic to calculate the number of bugs that have been fixed **by a release date** from the set of bugs that were originally open for that release.

## Filters and Fields Needed

To determine which bugs to include in the calculation, the following filters are applied:

1. **QA Whiteboard field**  
   - The QA Whiteboard is used to identify bugs that were open in a given release cycle.  
   - Example values:  
     ```
     [qa-found-in-c141] [qa-found-in-b141]
     ```  
   - These values indicate that the bug was open in release **141**.

2. **Tracking Flag Status**  
   - Each bug has a tracking flag for the corresponding Firefox release, e.g., `firefox141`.  
   - The status of this flag must be checked to determine whether the bug was marked as **verified/fixed**.
   - The version for each flag is extracted, 141, in this example to match it with the version each bug was logged in.

3. **Fix Date**  
   - The date when the tracking flag first changed to **verified/fixed** is required.  
   - This date (`flag_fixed_at`) is compared against the release date for that version.

4. **Release Cycle Comparison**  
   - A bug is counted as fixed by the release date only if its `flag_fixed_at` date is **within the release cycle**.  
   - If the fix landed after the release date, the bug does not count as fixed for that release.

## Example

| Field         | Value                  |
|---------------|------------------------|
| QA Whiteboard | `[qa-found-in-c141]`   |
| Tracking flag | `firefox141 → verified`|
| Flag fixed at | `2025-07-28`           |
| Release date  | `2025-07-22`           |
| **Result**    | ❌ Not fixed by release date (fix landed after release) |
