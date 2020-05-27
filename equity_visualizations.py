import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from solver import player_ev, hit_ev, stand_ev, double_ev, surrender_ev, split_ev


cols = player_ev.columns.tolist()[1:]

p_ev = pd.melt(player_ev, id_vars=["hand"], value_vars=cols, var_name="dealer")
h_ev = pd.melt(hit_ev, id_vars=["hand"], value_vars=cols, var_name="dealer")
s_ev = pd.melt(stand_ev, id_vars=["hand"], value_vars=cols, var_name="dealer")
d_ev = pd.melt(double_ev, id_vars=["hand"], value_vars=cols, var_name="dealer")
r_ev = pd.melt(surrender_ev, id_vars=["hand"], value_vars=cols, var_name="dealer")
spl_ev = pd.melt(split_ev, id_vars=["hand"], value_vars=cols, var_name="dealer")

ev = player_ev.set_index("hand")

actions = p_ev.copy()
actions.loc[actions.value == h_ev.value, "value"] = 'H'
actions.loc[actions.value == s_ev.value, "value"] = 'S'
actions.loc[actions.value == d_ev.value, "value"] = 'D'
actions.loc[actions.value == r_ev.value, "value"] = 'R'
actions.loc[actions.value == spl_ev.value, "value"] = 'P'

actions = pd.pivot(actions, index="hand", columns="dealer").value
actions = actions[ev.columns.tolist()]
actions = actions.reindex(player_ev.hand)
actions.columns.name = None 
actions.index.name = "Player's Hand" 

colormap = dict([(c, i) for i, c in enumerate(['H', 'S', 'D', 'R', 'P'])])
plt.rcParams.update({'font.size': 18, 'font.family': 'Futura', 'axes.labelpad': 15})
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(30, 24))
sns.heatmap(
    actions.replace(colormap),
    annot=actions.values,
    cmap=['springgreen', 'tomato', 'skyblue', 'plum', 'sandybrown'],
    fmt='', 
    ax=ax[0],
) 
cbar = ax[0].collections[0].colorbar 
r = cbar.vmax - cbar.vmin 
cbar.set_ticks([(r * i) + cbar.vmin for i in [.1, .3, .5, .7, .9]])
cbar.set_ticklabels(['Hit (H)', 'Stand (S)', 'Double (D)', 'Surrender (R)', 'Split (P)'])
cbar.ax.set_title("Action", pad=15)

sns.heatmap(
    ev.round(2),
    annot=True,
    cmap='RdYlGn',
    fmt='', 
    ax=ax[1],
) 

cbar = ax[1].collections[0].colorbar 
cbar.ax.set_title("Equity", pad=15)

for i in [0, 1]:
    ax[i].set_xticks(np.arange(ev.shape[1]) + 0.5, minor=False)
    ax[i].set_yticks(np.arange(ev.shape[0]) + 0.5, minor=False)
    ax[i].xaxis.tick_top() 
    ax[i].xaxis.set_label_position('top')
    ax[i].set_xticklabels(ev.columns.tolist(), minor=False)
    ax[i].set_yticklabels(ev.index.tolist(), minor=False)
    ax[i].tick_params(axis='y', labelrotation=0)
    ax[i].set_xlabel("Dealer's Upcard", size=20, labelpad=15, weight='semibold', family="Futura")
    ax[i].set_ylabel("Player's Hand", size=20, labelpad=15, weight='semibold', family="Futura")
    ax[i].figure.subplots_adjust(bottom = 0.5, top=0.9, left=0.2, right=0.8)
fig.patch.set_facecolor('seashell')
fig.patch.set_height(30)
fig.patch.set_width(40)
plt.tight_layout()
plt.subplots_adjust(top=0.9)
fig.suptitle('Blackjack Optimal Strategy', fontsize=45)
fig.savefig("images/optimal_actions.png", facecolor=fig.get_facecolor())


fig, ax = plt.subplots(figsize=(14, 18))
sns.heatmap(
    ev,
    annot=actions.values,
    cmap='RdYlGn',
    fmt='', 
    ax=ax,
) 
ax.set_xticks(np.arange(ev.shape[1]) + 0.5, minor=False)
ax.set_yticks(np.arange(ev.shape[0]) + 0.5, minor=False)
ax.xaxis.tick_top() 
ax.xaxis.set_label_position('top')
ax.set_xticklabels(ev.columns.tolist(), minor=False)
ax.set_yticklabels(ev.index.tolist(), minor=False)
ax.tick_params(axis='y', labelrotation=0)
ax.set_xlabel("Dealer's Upcard", size=20, labelpad=15, weight='semibold', family="Futura")
ax.set_ylabel("Player's Hand", size=20, labelpad=15, weight='semibold', family="Futura")
cbar = ax.collections[0].colorbar 
cbar.ax.set_title("Equity", pad=15)
fig.patch.set_facecolor('seashell')
plt.subplots_adjust(top=0.89, left=0.2)
fig.suptitle('Blackjack Optimal Strategy', fontsize=32)

plt.show()
fig.savefig("images/combined_equity.png", facecolor=fig.get_facecolor())
