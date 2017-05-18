#!/usr/bin/env python

import math
import random
import argparse
import numpy as np
import pandas as pd


parser = argparse.ArgumentParser(
        description='Generate a random practice schedule based on a pool of items in a spreadsheet.')

parser.add_argument(
    '-f',
    '--input-file',
    required=True,
    metavar='FILE',
    type=str,
    help='The spreadsheet file containing the practice items and category descriptions.')

parser.add_argument(
    '-o',
    '--output-csv-file',
    required=False,
    metavar='FILE',
    default=None,
    type=str,
    help='Filename that the random session will be written to in CSV format.')

parser.add_argument(
    '-d',
    '--duration',
    required=False,
    default=30,
    type=int,
    help='Session duration in integer minutes.')

parser.add_argument(
    '-b',
    '--padding',
    required=False,
    default=0,
    type=int,
    help='''Session padding time in minutes for each 30 minutes of the session.
    This time is subtracted from the time to be filled, in order to provide a
    buffer of time for changing between practice items.''')

parser.add_argument(
    '--category-limit-block-duration',
    required=False,
    default=None,
    type=int,
    help='''If this value is specified, then the per-category item limits are
    interpreted as limits per each N-minute block of time, rather than being
    applied as hard limits on the number of per-category items for the entire
    session.''')

parser.add_argument(
    '--ignore-category-min-counts',
    required=False,
    default=False,
    action='store_true',
    help='''Ignore the per-category minimum item counts.''')

parser.add_argument(
    '--ignore-category-max-counts',
    required=False,
    default=False,
    action='store_true',
    help='''Ignore the per-category maximum item counts.''')

parser.add_argument(
    '--ignore-essential-flag',
    required=False,
    default=False,
    action='store_true',
    help='''Ignore the essential flag when selecting items.''')

args = parser.parse_args()
input_file = args.input_file
session_output_file = args.output_csv_file
total_time_minutes = args.duration
buffer_time_per_30_minutes = args.padding
category_item_limits_time_block_minutes = args.category_limit_block_duration

# Derived configuration items
buffer_time = math.ceil(total_time_minutes / 30 * buffer_time_per_30_minutes)
practice_time_minutes = total_time_minutes - buffer_time

# Data load
categories = pd.read_excel(
    input_file,
    sheetname='categories',
    index_col=0,
    converters=
    {
        'min_items': int,
        'max_items': int,
    })

data = pd.read_excel(
    input_file,
    sheetname='items',
    converters=
    {
        'min_time': int,
        'max_time': int,
        'priority': float,
        'essential': bool,
        'tempo': str,
        'notes': str,
    })

# Fill missing values with defaults
data.weight = data.weight.fillna(1)
data.min_time = data.min_time.fillna(2)
data.max_time = data.max_time.fillna(5)
data.sort_order = data.sort_order.fillna(2)
data.tempo = data.tempo.fillna('')
data.notes = data.notes.fillna('')

# if required, scale the category max item counts by the block time
if category_item_limits_time_block_minutes:
    category_item_limit_scale = max(1, round(practice_time_minutes / category_item_limits_time_block_minutes))
    categories.min_items *= category_item_limit_scale
    categories.max_items *= category_item_limit_scale

# Generate the random item times
def generate_random_times(df):
    return pd.DataFrame(
        {'time': df.apply(lambda row: random.randrange(row.min_time, row.max_time+1), axis=1)},
        index=df.index)

data = data.join(generate_random_times(data))

# clear the essential flag if requested
if args.ignore_essential_flag:
    data.essential = False

# Seed the session with essential items
session = data.query('essential == True')

# select the set of candidate items
items = data.query('essential == False and weight > 0')

# initial sampling to meet the minimum item count per category constraint
if not args.ignore_category_min_counts:
    for category, group in items.groupby('category'):
        # For this category, attempt to select the min number of items
        try:
            min_items = categories.loc[category].min_items
            current = len(session[session.category == category])
            required = min(min_items - current, len(group))
            if not np.isnan(required) and required > 0:
                new_items = group.sample(n=required, weights='weight')
                items = items.drop(new_items.index)
                session = session.append(new_items)
        except:
            pass

# Fill the rest of the session
while session.time.sum() < practice_time_minutes and len(items) > 0:
    # Clean out any maxed categories from the candidate items
    for category, group in items.groupby('category'):
        current_items_in_category = len(session[session.category == category])
        max_category = categories.loc[category].max_items
        if (not args.ignore_category_max_counts
            and not np.isnan(max_category)
            and current_items_in_category >= max_category):
            print('Category "{0}" reached maximum item count ({1})'.format(
                category, max_category))
            items = items[items.category != category]

    # only query candidates where the min time can fit into the remaining time
    remaining_time = practice_time_minutes - session.time.sum()
    candidates = items.query('min_time <= {0}'.format(remaining_time))

    # If no candidates left, we must abort
    if len(candidates) == 0:
        print('unable to fill session')
        break

    # pick the next item
    i = candidates.sample(n=1, weights='weight')

    item_time = i.time.iloc[0]
    item_min_time = i.min_time.iloc[0]
    item_max_time = i.max_time.iloc[0]

    if item_time <= remaining_time:
        # if the item fits, use it
        session = session.append(i)
        items = items.drop(i.index)
    else:
        # trim the item time to the remaining (without exceeding item cap)
        print('setting time to remaining')
        i.loc[:,'time'] = min(remaining_time, item_max_time)
        session = session.append(i)
        items = items.drop(i.index)

# Final Shuffle
# Shuffle the items within each sort_order group, while still respecting the
# sort order overall. This prevents essential items always appearing at the
# start of the session.
session['r'] = np.random.uniform(size=len(session))
session.sort_values(by=['sort_order', 'r'], inplace=True)

# Output the results
session_time = session.time.sum()
print('Planned total time: {0}'.format(total_time_minutes))
print('Estimated total time: {0}'.format(session_time + buffer_time))
print('Session time: {0}'.format(session_time))
print('Planned time buffer: {0}'.format(buffer_time))

display_session = session[['name', 'category', 'tempo', 'notes', 'time']]
display_session.columns = ['Name', 'Category', 'Tempo', 'Notes', 'Duration']
print(display_session)

display_session.to_csv(
    session_output_file,
    index=False,
    index_label=False,
    encoding='utf-8')

