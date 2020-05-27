import numpy as np
import pandas as pd

soft_cutoff = 17

# The dealer can only end up in 6 possible end states: 17, 18, 19, 20, 21, and BUST
final_states = {"BUST": 0, 17: 1, 18: 2, 19: 3, 20: 4, 21: 5}

# Max state the dealer can enter is 26
dealer_states = np.zeros((6, 27))
# Max state where A=11 is 21
soft_equity = np.zeros((6, 22))

# Compute the probability that the dealer enters each final state from the current state
for state, i in final_states.items():
    if state != "BUST":
        dealer_states[i, state] = 1
        soft_equity[i, state] = 1
    else:
        dealer_states[i, 22:] = 1

for state in range(16, 0, -1):
    # Compute the equity of drawing a 2-9
    low_card_equity = dealer_states[:, state + 2: state + 10].sum(axis=1)
    # Compute the equity of drawing T, J, Q, or K
    high_card_equity = dealer_states[:, state + 10] * 4
    # Compute the equity of drawing an A (Assume the dealer stays on a soft 17)
    # If the dealer's value is between 7 and 10 (inclusive), he will stand after hitting an A 
    if state >= soft_cutoff - 11 and state <= 10:
        ace_equity = dealer_states[:, state + 11]
    # If the dealer's value is greater than 11, the A will be treated as a 1
    elif state >= 11:
        ace_equity = dealer_states[:, state + 1]
    # If the dealer's value is less than 6, we need to compute whether it will be a 1 or an 11
    else:
        soft_value = state + 11
        N = 21 - soft_value 
        a11_equity = soft_equity[:, soft_value + 1: 22].sum(axis=1)
        a1_equity = dealer_states[:, state + N + 2: state + 11].sum(axis=1)
        ace_equity = (a11_equity + a1_equity + dealer_states[:, soft_value] * 4) / 13
        soft_equity[:, soft_value] = ace_equity
    dealer_states[:, state] = (low_card_equity + high_card_equity + ace_equity) / 13


# The probabilities are the same for cards 2-9, but not for any 10 or A
# If the dealer shows a 10 or an A it's impossible for him to have 21 if the game continues
dealer_starting_states = dealer_states[:, :12]
dealer_starting_states[:, 10] = (dealer_states[:, 12: 20].sum(axis=1) + dealer_states[:, 20] * 4) / 12
dealer_starting_states[:, 11] = soft_equity[:, 12: 21].sum(axis=1) / 9


# Compute the EVs for standing at all hard states for the player
player_hard_stand_ev = np.zeros((32, 12))
player_hard_stand_ev[:17] = -dealer_starting_states[1:].sum(axis=0) + dealer_starting_states[0]
for state in range(17, 21):
    i = final_states[state]
    losing_ev = dealer_starting_states[i+1:].sum(axis=0)
    winning_ev = dealer_starting_states[:i].sum(axis=0)
    player_hard_stand_ev[state] = winning_ev - losing_ev 
player_hard_stand_ev[21:] = dealer_starting_states[:final_states[21]].sum(axis=0)
player_hard_stand_ev[22:] = -1 


# Compute the EVs for standing at all soft states for the player
player_soft_stand_ev = np.zeros((32, 12))
player_soft_stand_ev[:22] = player_hard_stand_ev[:22] 
player_soft_stand_ev[22:] = player_hard_stand_ev[12:22] 


# Create the master EV tables
player_hard_ev = np.zeros((32, 12))
player_hard_ev[21:] = player_hard_stand_ev[21:]

player_soft_ev  = np.zeros((22, 12))
player_soft_ev[21] = player_soft_stand_ev[21]


# Compute the EVs for standing at all hard states for the player
player_hard_hit_ev = np.zeros((32, 12))
player_hard_hit_ev[21:] = -1 

player_soft_hit_ev = np.zeros((32, 12))

for state in range(20, 0, -1):
    # Compute the equity of drawing a 2-9
    low_card_equity = player_hard_ev[state + 2: state + 10].sum(axis=0)
    # Compute the equity of drawing T, J, Q, or K
    high_card_equity = player_hard_ev[state + 10] * 4
    # Compute the equity of drawing an A
    # If the player's value is >= 11, an A will be worth 1 
    if state >= 11:
        ace_equity = player_hard_ev[state + 1]
    # If the player's score is less than 11, then he will have a soft score after hitting an A
    else:
        soft_value = state + 11
        N = 21 - soft_value 
        a11_equity = player_soft_ev[soft_value + 1: 22].sum(axis=0)
        a1_equity = player_hard_ev[state + N + 2: state + 11].sum(axis=0)
        player_soft_hit_ev[soft_value] = (a11_equity + a1_equity + player_hard_ev[soft_value] * 4) / 13
        ace_equity = np.maximum(player_soft_hit_ev[soft_value], player_soft_stand_ev[soft_value]) 
        player_soft_ev[soft_value] = ace_equity
    player_hard_hit_ev[state] = (low_card_equity + high_card_equity + ace_equity) / 13
    player_hard_ev[state] = np.maximum(player_hard_hit_ev[state], player_hard_stand_ev[state])

# Compute the EV of doubling the initial bet
player_hard_double_ev = np.zeros((22, 12))
player_hard_double_ev[21] = -2
for state in range(4, 21):
    low_card_equity = player_hard_stand_ev[state + 2: state + 10].sum(axis=0)
    high_card_equity = player_hard_stand_ev[state + 10] * 4
    ace_equity = player_soft_stand_ev[state + 11]
    player_hard_double_ev[state] = 2 * (low_card_equity + high_card_equity + ace_equity) / 13

player_soft_double_ev = np.zeros((22, 12))
for state in range(12, 22):
    low_card_equity = player_soft_stand_ev[state + 1: state + 10].sum(axis=0) 
    high_card_equity = player_soft_stand_ev[state + 10] * 4
    player_soft_double_ev[state] = 2 * (low_card_equity + high_card_equity) / 13 

# The expected value of surrendering is always -0.5
hard_surrender_ev = np.zeros((22, 12)) - 0.5
soft_surrender_ev = np.zeros((22, 12)) - 0.5

# Update the EV tables based on these results
player_hard_ev[4: 22] = np.maximum(player_hard_ev[4: 22], player_hard_double_ev[4: 22])
player_soft_ev[12: 22] = np.maximum(player_soft_ev[12: 22], player_soft_double_ev[12: 22])
player_hard_ev[4: 22] = np.maximum(player_hard_ev[4: 22], hard_surrender_ev[4: 22])
player_soft_ev[12: 22] = np.maximum(player_soft_ev[12: 22], soft_surrender_ev[12: 22])

# Compute the EV of making a split
split_ev = np.zeros((12, 12))
for state in range(2, 11):
    low_card_equity = player_hard_ev[state + 2: state + 10].sum(axis=0)
    high_card_equity = player_hard_ev[state + 10] * 4
    if state < 11:
        ace_equity = player_soft_ev[state + 11]
    split_ev[state] = 2 * (low_card_equity + high_card_equity + ace_equity) / 13
split_ev[11] = 2 * (player_soft_stand_ev[12: 21].sum(axis=0) + player_soft_stand_ev[21] * 4) / 13

player_split_ev = split_ev.copy()

for state in range(2, 11):
    player_split_ev[state] = np.maximum(player_split_ev[state], player_hard_ev[2 * state])
player_split_ev[11] = np.maximum(player_split_ev[11], player_soft_ev[12])

# Add split data to all other tables
def get_split_table(ev_table_h, ev_table_s):
    args = []
    for i in range(11):
        args.append(ev_table_h[2*i])
    args.append(ev_table_s[12])
    return np.stack(tuple(args), axis=0)

player_split_stand_ev = get_split_table(player_hard_stand_ev, player_soft_stand_ev)
player_split_hit_ev = get_split_table(player_hard_hit_ev, player_soft_hit_ev)
player_split_double_ev = get_split_table(player_hard_double_ev, player_soft_double_ev)
split_surrender_ev = get_split_table(hard_surrender_ev, soft_surrender_ev)


# Put all of our results into nice tables


def stack_equities(hard, soft, split):
    dealer_hands = list(range(2, 10)) + ['T', 'A']
    soft_hands = [f"A{x}" for x in range(2, 10)]
    split_hands = [f"{h}{h}" for h in dealer_hands]
    player_hands = list(range(4, 22)) + soft_hands + split_hands
    index_to_hand = dict(enumerate(player_hands)) 
    args = (hard[4:22, 2:12], soft[13:21, 2:12], split[2:12:, 2:12])
    data = np.concatenate(args, axis=0)
    df = (
        pd.DataFrame(data, columns=dealer_hands)
        .reset_index()
        .rename(columns={"index": "hand"})
    )
    df.hand = df.hand.map(index_to_hand)
    return df

player_ev = stack_equities(player_hard_ev, player_soft_ev, player_split_ev)
stand_ev = stack_equities(
    player_hard_stand_ev, player_soft_stand_ev, player_split_stand_ev
)
hit_ev = stack_equities(
    player_hard_hit_ev, player_soft_hit_ev, player_split_hit_ev
)
double_ev = stack_equities(
    player_hard_double_ev, player_soft_double_ev, player_split_double_ev
)
surrender_ev = stack_equities(
    hard_surrender_ev, soft_surrender_ev, split_surrender_ev 
)
split_ev = stack_equities(
    -np.ones(player_hard_ev.shape), -np.ones(player_soft_ev.shape), split_ev
)
