# practice-randomiser

Randomised music practice session generator.

Although I am writing this to generate guitar practice sessions, it could be
used for any instrument. For that matter, it could be used to generate
a randomised subset of items for any sort of practice schedule.

## Usage

Use the sample spreadsheet as a guide to configuring the range of possible items
to include in the randomised session.

### Spreadsheet Columns

#### items sheet

The items sheet determines the individual practice items that can be considered
for inclusion in a practice session.

You can also omit the **category** column, and instead have a separate sheet
for each category. In this case, you must pass the `--one-category-per-sheet`
argument.

* **name**: Item name used in the session output.
* **category**: Category of the item.
* **tempo**: Descriptive field that isn't used in the randomisation algorithm. This field is used in the
  [Countdown.net](https://github.com/DC23/countdown.net) project to render the
  item tempo in a different font to the item notes.
* **notes**: Descriptive field that isn't used in the randomisation algorithm.
  Use for additional notes you want displayed alongside each item.
* **min_time**: Minimum time for the practice item.
* **max_time**: Maximum time for the practice item.
* **sort_order**: Sorting order. Items in the final session are sorted into
  ascending order based on this field. Allows control over where in the random
  session items are placed. Does not control whether a given item is selected or
  not.
* **essential**: Forces selection of the item. Note that excessive use of this
  constraint may lead to session times that exceed the target time.
* **weight**: Influences the likelihood of an item being selected. A weight of
  2 is twice as likely to be selected as a weight 1 item. Weight 0 items will be
  excluded from consideration. Think of the weight as the number of lottery
  tickets each item has in the draw.

#### __metadata__ sheet

* **name**: Category name. Should match the categories used in the `items` sheet (or in the category sheet names).
* **min_items**: Minimum items to use from the category.
* **max_items**: Maximum number of items to include from the category.

### Command-line arguments

There are a number of command-line arguments that allow you to modify the
application of item and category constraints specified in the input file.

```bash
usage: practice-randomiser.py [-h] -f FILE [-o FILE] [-d DURATION]
                              [-b PADDING]
                              [--category-limit-block-duration CATEGORY_LIMIT_BLOCK_DURATION]
                              [--ignore-category-min-counts]
                              [--ignore-category-max-counts]
                              [--ignore-essential-flag]

Generate a random practice schedule based on a pool of items in a spreadsheet.

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --input-file FILE
                        The spreadsheet file containing the practice items and
                        category descriptions.
  -o FILE, --output-csv-file FILE
                        Filename that the random session will be written to in
                        CSV format.
  -d DURATION, --duration DURATION
                        Session duration in integer minutes.
  -b PADDING, --padding PADDING
                        Session padding time in minutes for each 30 minutes of
                        the session. This time is subtracted from the time to
                        be filled, in order to provide a buffer of time for
                        changing between practice items.
  --category-limit-block-duration CATEGORY_LIMIT_BLOCK_DURATION
                        If this value is specified, then the per-category item
                        limits are interpreted as limits per each N-minute
                        block of time, rather than being applied as hard
                        limits on the number of per-category items for the
                        entire session.
  --ignore-category-min-counts
                        Ignore the per-category minimum item counts.
  --ignore-category-max-counts
                        Ignore the per-category maximum item counts.
  --ignore-essential-flag
                        Ignore the essential flag when selecting items.
  --one-category-per-sheet
                        Use the new-style one category per worksheet.

```

## Example Run

```shell
python practice-randomiser.py -f practice_elements.xlsx -d 30 -b 5
```

produces

```bash
Category "repertoire" reached maximum item count (1)
setting time to remaining
Planned total time: 30
Estimated total time: 30
Session time: 25
Planned time buffer: 5
             Name       Category     Tempo                                     Notes  Duration
5   must do first      technique                                                             2
12             s2  sight reading                                                             5
6              t2      technique                                                             1
4              p5        pattern                                                             5
1              p2        pattern  80 – 140  Watch the transition from 4 to 6 strings         2
3              p4        pattern                                                             3
7              t3      technique                                                             2
10             r1     repertoire                                                             5
```