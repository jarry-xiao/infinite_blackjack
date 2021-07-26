#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import pandas as pd


# In[2]:


class Deck:
    def __init__(self, missing):
        self.base_deck = [16,4,4,4,4,4,4,4,4,4]
        if len(missing) < 10:
            missing = missing + [0] * (10 - len(missing))
        self.missing = missing
    
    def get_remaining(self):
        return [bd - m for bd, m in zip(self.base_deck, self.missing)]
    
    def get_possible(self):
        return [i for i in self.get_remaining() if i > 0]
    
    def get(self, card, exclude=None):
        if exclude is not None:
            if card == exclude:
                return 0
            else:
                odds = self.get_remaining()[card] / (sum(self.get_remaining()) - self.get_remaining()[exclude])
        else:
            if sum(self.get_remaining()) == 0:
                print(self.missing)
                return 0
            odds = self.get_remaining()[card] / sum(self.get_remaining())
            
        return odds


# In[3]:


class Hand:
    def __init__(self, hand):
        if len(hand) < 10:
            hand = hand + [0] * (10 - len(hand))
        self.hand = hand
        
    def score(self):
        score = 0
        for i, val in enumerate(self.hand):
            if i == 0:
                score += 10 * val
            else:
                score += i * val
                
        if (self.hand[1] > 0) & (score <= 11):
            return (10 + score, True)
        else:
            return (score, False)


# In[4]:


class Leaf:
    def __init__(self, hand, deck, odds):
        self.odds = odds
        self.hand = hand
        self.missing = deck.missing.copy()
        self.deck = Deck(deck.missing.copy())
        self.children = []
        
        for i in range(10):
            hand = Hand(self.hand.hand.copy())
            hand.hand[i] += 1
            odds = self.deck.get(i) * self.odds
            score = hand.score()[0]
            is_soft = hand.score()[1]
            self.missing[i] += 1
            
            if odds == 0:
                self.children.append(None)
            elif score > 21:
                self.children.append((0, odds))
            elif score > 17:
                self.children.append((score, odds))
            elif (score == 17) & (is_soft == False):
                self.children.append((score, odds))
            else:
                self.children.append(Leaf(hand, Deck(self.missing.copy()), odds))

class Root:
    def __init__(self, upcard, deck, odds):
        self.odds = odds
        self.upcard = upcard
        self.hand = Hand([])
        self.hand.hand[upcard] += 1
        self.missing = deck.missing.copy()
        self.deck = deck
        self.children = []
        
        for i in range(10):
            if self.upcard <= 1:
                hand = Hand(self.hand.hand.copy())
                hand.hand[i] += 1
                odds = self.deck.get(i, exclude=1-self.upcard) * self.odds
                score = hand.score()[0]
                is_soft = hand.score()[1]
                self.missing[i] += 1

                if odds == 0:
                    self.children.append(None)
                elif score > 21:
                    self.children.append((0, odds))
                elif score > 17:
                    self.children.append((score, odds))
                elif (score == 17) & (is_soft == False):
                    self.children.append((score, odds))
                else:
                    self.children.append(Leaf(hand, Deck(self.missing.copy()), odds))
            else:
                hand = Hand(self.hand.hand.copy())
                hand.hand[i] += 1
                odds = self.deck.get(i) * self.odds
                score = hand.score()[0]
                is_soft = hand.score()[1]
                self.missing[i] += 1

                if odds == 0:
                    self.children.append(None)
                elif score > 21:
                    self.children.append((0, odds))
                elif score > 17:
                    self.children.append((score, odds))
                elif (score == 17) & (is_soft == False):
                    self.children.append((score, odds))
                else:
                    self.children.append(Leaf(hand, Deck(self.missing.copy()), odds))              
            

        


# In[5]:


class SearchTree:
    def __init__(self, upcard, missing):
        self.upcard = upcard
        self.deck = Deck(missing)
        self.missing = self.deck.missing
        self.deck.missing[self.upcard] += 1
        
    def get_outcomes(self):
        outcomes = {}
        stack = [Root(self.upcard, self.deck, 1)]
        
        while(len(stack) > 0):
            node = stack.pop(-1)
            if node is not None:
                if isinstance(node, Leaf) | isinstance(node, Root):  
                    for child in node.children:
                        stack.append(child)
                else:
                    if node[0] in outcomes.keys():
                        outcomes[node[0]] += node[1]
                    else:
                        outcomes[node[0]] = node[1]
        return outcomes
        


# In[6]:


def dealer_cache_key(upcard, missing):

    return str(upcard) + str(missing)

def dealer_outcomes(upcard, missing):
    if dealer_cache_key(upcard, missing) in dealer_cache.keys():
        return dealer_cache[dealer_cache_key(upcard, missing)]
    else:
        s = SearchTree(upcard, missing)
        outcomes = s.get_outcomes()
        dealer_cache[dealer_cache_key(upcard, missing)] = outcomes
        return outcomes

def player_cache_key(cards, upcard, remove = []):
    card_list = [0] * 10
    for card in cards:
        card_list[card] += 1
    remove_list = [0] * 10
    for r in remove:
        remove_list[r] += 1
    
    return str(upcard) + str(card_list) + str(remove_list)
    
    


# In[7]:


class Player:
    def __init__(self, cards):
        self.cards = cards
        self.cache = {}
    
    def ev(self, upcard, remove=[]):
        
        return self.act(self.cards, upcard, top_level=True, remove=remove)[1]
    
    def action(self, upcard, remove=[]):
        
        return self.act(self.cards, upcard, top_level=True, remove=remove)[0]
    
    def cache_key(self, cards, upcard):
        
        h = Hand([])
        for card in cards:
            h.hand[card] += 1
        string_list = [str(upcard)] + [str(i) for i in h.hand]
        
        return "".join(string_list)
        
        
    def winrate(self, score, outcomes):
        
        if score > 21:
            return 0
        
        winrate = 0
        for key, value in outcomes.items():
            if score > key:
                winrate += value
            elif score == key:
                winrate += value / 2
                
        return winrate
        
    
    def act(self, cards, upcard, top_level=False, remove=[]):
        
        if top_level:
            print(f"Player Cards: {cards}, Dealer Card: {upcard}")
            
        pck = player_cache_key(cards, upcard, remove.copy())
        if pck in player_cache.keys():
            split = player_cache[pck]["split"]
            hit = player_cache[pck]["hit"]
            stay = player_cache[pck]["stay"]
            double = player_cache[pck]["double"]
        else:
            split = self.split(cards, upcard, remove=remove.copy())
            hit = self.hit(cards, upcard, remove=remove.copy())
            stay = self.stay(cards, upcard, remove=remove.copy())
            double = self.double(cards, upcard, remove=remove.copy())
            
            player_cache[pck] = {
                "split" : split,
                "hit": hit,
                "stay": stay,
                "double": double
            }
        
        
        best_ev = max([split, hit, stay, double])
        if best_ev == split:
            best = "Split"
        if best_ev == hit:
            best = "Hit"
        if best_ev == stay:
            best = "Stay"
        if best_ev == double:
            best = "Double"
        
        
        h = Hand([])
        for card in cards:
            h.hand[card] += 1
        score = h.score()[0]
        is_soft = h.score()[1]
        soft = ""
        if is_soft:
            soft = "Soft "
        
        if top_level:
            print(f"Split: {split}, Hit: {hit}, Stay: {stay}, Double: {double}")
            print(best, best_ev)
        
        return (best, best_ev)
        
    
    def split(self, cards, upcard, remove=[]):
        
        # For now assuming deck is duplicated at split time with both cards removed
        
        
        if len(cards) > 2:
            return 0
        
        if cards[0] != cards[1]:
            return 0
        
        remove = remove.copy() + [cards[0]]
        winrate = self.hit([cards[0]], upcard, remove=remove)
        return 2 * winrate - 0.5
        
        
        
    
    def hit(self, cards, upcard, remove=[]):
        
        
        h = Hand([])
        d = Deck([])
        
        for card in cards:
            h.hand[card] += 1
            d.missing[card] += 1
        
        
        for r in remove:
            d.missing[r] += 1
        
            
        profit = 0
        for i in range(10):
            d.missing[upcard] += 1
            odds = d.get(i)
            d.missing[upcard] -= 1
            h.hand[i] += 1
            
            if odds > 0:
                
                if h.score()[0] > 21:
                    profit += 0
                elif h.score()[0] == 21:
                    profit += odds * (self.act(cards + [i], upcard, remove=remove.copy())[1])
                else:
                    profit += odds * (self.act(cards + [i], upcard, remove=remove.copy())[1])
            
            h.hand[i] -= 1
        
        return profit
    
    
    def stay(self, cards, upcard, remove=[]):
        
        d = Deck([])
        h = Hand([])
        for card in cards:
            d.missing[card] += 1
            h.hand[card] += 1
        
        for r in remove:
            d.missing[r] += 1
            
        score = h.score()[0]
        outcomes = dealer_outcomes(upcard, d.missing.copy())
        
        return self.winrate(score, outcomes)
        
        
    def double(self, cards, upcard, remove=[]):
        
        
        
        if len(cards) > 2:
            return 0
        
        h = Hand([])
        d = Deck([])
        for card in cards:
            h.hand[card] += 1
            d.missing[card] += 1

        for r in remove:
            d.missing[r] += 1
            
        ev = 0
        for i in range(10):
            d.missing[upcard] += 1
            odds = d.get(i)
            d.missing[upcard] -= 1
            h.hand[i] += 1
            d.missing[i] += 1
            if odds > 0:
                winrate = self.winrate(h.score()[0], dealer_outcomes(upcard, d.missing.copy()))
                profit = 2 * winrate - 0.5
                ev += odds * profit
            h.hand[i] -= 1
            d.missing[i] -= 1
        
        return ev
        


# In[8]:


with open("files/dealer_cache.json") as file:
    dealer_cache = json.load(file)
with open("files/player_cache.json") as file:
    player_cache = json.load(file)


# In[9]:


def solve(card1, card2, upcard, remove=[]):
    p = Player([card1, card2])
    return p.act(p.cards, upcard, remove=[], top_level=True)


# In[10]:


# action_dict = {}
# for card1 in range(10):
#     action_dict
#     for card2 in range(card1 + 1):
#         action_dict[(card1,card2)] = {}
#         if card1 + card2 != 1:
#             for upcard in range(10):
#                 action_dict[(card1,card2)][upcard] = solve(card1,card2,upcard)


# In[11]:


# with open("files/player_cache.json", "w") as output:
#     json.dump(player_cache, output)

# with open("files/dealer_cache.json", "w") as output:
#     json.dump(dealer_cache, output)

# In[12]:

# df = pd.DataFrame(columns=[i for i in range(10)], index=action_dict.keys())
# for key,value in action_dict.items():
#     row = [""] * 10
#     for k,v in value.items():
#         row[k] = v
        
#     df.loc[key] = row
# df.to_csv("solution.csv")
