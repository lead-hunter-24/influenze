"""
Generate a UNIVERSAL-SCHEMA channel data file for the YT Insights app.

The schema below is channel-agnostic: every metric is derivable for ANY YouTube
channel from (a) channel stats and (b) a list of videos. Drop a new channel's
raw data into RAW_CHANNELS and re-run to add it to the app.

Universal variables
===================
Channel level:
  identity    : channelId, handle, title, createdAt, channelAgeDays, topics
  scale       : subscribers, totalViews, totalVideos
  efficiency  : avgViewsPerVideo, viewsPerSubscriber, uploadsPerMonth
  momentum    : subsGained30d, viewsGained30d, videosPublished30d
Video level (per video):
  identity    : videoId, title, publishedAt, ageDays, topic
  format      : durationSeconds, durationMin, titleHasNumber, titleWordCount
  reach       : views
  reaction    : likes, comments
  derived     : engagementRate, likeRate, commentRate,
                viewsPerDay (velocity), outlierMultiple (views / channel median)
Aggregates (computed):
  medianViews, medianEngagement, top3ViewShare,
  topicAggregates[{topic, count, totalViews, avgViews}]
"""
import json, re, os, statistics
from datetime import date

CAPTURE = date(2026, 6, 20)
OUTDIR = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# RAW DATA  (source: vidiq, captured 2026-06-20). Add more channels here.
# ---------------------------------------------------------------------------
RAW_CHANNELS = {
    "crayon_capital": {
        "channel": {
            "channelId": "UCP9RPj_BG0vit2TNM7LuRxA",
            "handle": "@Crayon_Capital",
            "title": "Crayon Capital",
            "createdAt": "2025-03-31",
            "topics": ["Society", "Knowledge"],
            "subscribers": 219000,
            "totalViews": 15712554,
            "totalVideos": 23,
            "subsGained30d": 6000,
            "viewsGained30d": 554808,
            "videosPublished30d": 2,
        },
        # videoId, title, publishedAt, durationISO, views, likes, comments, topic
        "videos": [
            ("3QE_q7-cqGI", "Why The Richest Company In History Went Bankrupt", "2026-06-15", "PT15M42S", 38112, 1465, 90, "Business / Biography"),
            ("A_wtItX_kIE", "The Biggest Lie in Economics (And You Still Believe It)", "2026-05-23", "PT13M22S", 27671, 1048, 83, "Economics"),
            ("9r-45QPLl-Y", "Petrodollar Explained Like You're 5", "2026-04-30", "PT11M20S", 165706, 5544, 329, "Geopolitics"),
            ("wu1GfDhAYvE", "Iran War Explained Like You're 5", "2026-04-19", "PT12M11S", 135202, 5282, 658, "Geopolitics"),
            ("adpt6KW4Jb4", "Margin Call Scandal Explained Like You're 5", "2026-03-30", "PT13M45S", 122207, 3360, 264, "Fraud & Scandal"),
            ("wOjdbltaXSQ", "The Worst Time to be Rich as a Human", "2026-03-09", "PT20M29S", 377883, 12440, 821, "Economics"),
            ("sMH8WchxQR8", "Rockefeller: The First Confirmed Billionaire (And How He Did It)", "2026-02-28", "PT20M16S", 1021813, 19351, 527, "Business / Biography"),
            ("RB-DTXw1Yzw", "Xi Jinping: The Most Powerful Man in China", "2026-02-10", "PT21M1S", 200051, 5501, 432, "Geopolitics"),
            ("GPgaG9D7S6I", "5000 Years of Gold Explained in 16 Minutes", "2026-01-31", "PT16M6S", 131260, 3773, 345, "Economics"),
            ("GSkySDNmjV8", "Palantir Technologies Explained Like You're 5", "2026-01-10", "PT15M19S", 664144, 18911, 1129, "Technology / Business"),
            ("y51JjcymEAY", "The Man Who Built Singapore in One Generation", "2025-12-27", "PT16M9S", 767751, 17398, 1167, "Geopolitics"),
            ("kx_okFl98Vw", "The AI Bubble Explained Like You're 5", "2025-12-12", "PT12M13S", 396090, 12406, 714, "Technology / Business"),
            ("rSgS4wNLLDM", "How Jeff Bezos Actually Built Amazon", "2025-11-28", "PT20M13S", 875812, 17060, 617, "Business / Biography"),
            ("CCXYfrAfW6g", "The Day the Internet Almost Died", "2025-10-27", "PT12M9S", 362709, 9824, 380, "Technology / Business"),
            ("HawmGu7oNrc", "The Wolf of Wall Street Scam Explained Like You're 5", "2025-10-03", "PT16M33S", 4122583, 77593, 3268, "Fraud & Scandal"),
            ("p9x9s_-IOOM", "The $9 Billion Blood Test That Never Worked (Theranos)", "2025-09-08", "PT16M21S", 211186, 4593, 359, "Fraud & Scandal"),
            ("LuEcoqizj0o", "The Great Depression Explained Like You're 5", "2025-08-15", "PT16M29S", 2606358, 42703, 2807, "Economic History"),
            ("VSbO8vmZNm0", "The $63 BILLION Company That Sold Nothing", "2025-07-19", "PT13M13S", 855267, 18035, 1150, "Fraud & Scandal"),
            ("_pUOpoihjA4", "Bitcoin Explained Like You're 5", "2025-07-12", "PT10M15S", 103234, 2890, 229, "Economics"),
            ("EedHneVKmpo", "The Rise of Paypal Explained Like You're 5", "2025-06-25", "PT12M36S", 91407, 3185, 96, "Technology / Business"),
            ("KE-WJevx-7c", "The 2008 Financial Crisis Explained Like You're 5", "2025-06-15", "PT13M26S", 2205557, 47994, 2889, "Economic History"),
            ("xhbukTTkwJY", "How One Man Pulled Off a $65 Billion Scam", "2025-05-08", "PT11M34S", 182486, 4549, 215, "Fraud & Scandal"),
            ("KHLY6SyLvgQ", "Every Financial Crisis Explained in 10 Minutes", "2025-04-22", "PT10M54S", 61803, 1631, 60, "Economic History"),
        ],
    },
    "hypothetically": {
        "channel": {
            "channelId": "UC0L9hD7HMwWU7xuU5HRA6Iw",
            "handle": "@HypotheticallyHQ",
            "title": "Hypothetically",
            "createdAt": "2023-10-27",
            "topics": ["Entertainment", "Society", "Knowledge"],
            "subscribers": 297000,
            "totalViews": 25183421,
            "totalVideos": 33,
            "subsGained30d": 16000,
            "viewsGained30d": 1579296,
            "videosPublished30d": 3,
        },
        "videos": [
            ("81r4BT3Wm5E", "POV: You're a Prehistoric Human", "2026-06-17", "PT15M55S", 32215, 1864, 292, "Survival & Sci-Fi"),
            ("GczRApVP5jo", "Could You Survive the Dinosaur Era?", "2026-06-05", "PT20M24S", 46354, 2146, 340, "Survival & Sci-Fi"),
            ("6k6QjHtRHYk", "The Wealth Explainer is DEAD", "2026-05-23", "PT50S", 126405, 6392, 733, "Channel / Meta"),
            ("vbm53rwV5bM", "What It's Like to be The Most Famous Person Alive", "2026-05-20", "PT16M49S", 91484, 3541, 421, "Life & Fame"),
            ("Sl54QoJgXJg", "What Superpowers Would ACTUALLY Feel Like", "2026-05-07", "PT14M48S", 631760, 19806, 1050, "Survival & Sci-Fi"),
            ("xjc5u6UK7-s", "POV: You Wake Up in the Year 2526", "2026-04-26", "PT18M19S", 337560, 9191, 915, "Survival & Sci-Fi"),
            ("OPjgV5spyWM", "POV: You're a Trillionaire", "2026-04-13", "PT16M8S", 1988682, 48682, 3216, "Wealth & Money"),
            ("ISrPsyv5MsE", "What Day 1 of the Zombie Apocalypse Would Be Like", "2026-03-28", "PT17M3S", 752736, 22036, 1413, "Survival & Sci-Fi"),
            ("HByY2gb1llw", "What if you were undercover in the KKK?", "2026-03-17", "PT18M36S", 631315, 14403, 774, "Crime & Underworld"),
            ("_pDRBnQHsMI", "Your Life as Every Squid Games Rank", "2026-03-09", "PT14M34S", 250125, 6216, 387, "Ranks & Hierarchy"),
            ("xPzwR_Y698o", "What It's Like to Be a Black Market Surgeon", "2026-02-28", "PT16M27S", 5167636, 125993, 3688, "Crime & Underworld"),
            ("o83MjZlCzM8", "What It Was Like to Be Every Spartan Rank", "2026-02-27", "PT14M", 101046, 2456, 123, "Ranks & Hierarchy"),
            ("A5mmQQiywfg", "What It Was Like to be a Scammer in 1889", "2026-02-23", "PT11M30S", 87583, 2262, 219, "Crime & Underworld"),
            ("tEaFfG081HQ", "What It's Like to Be a Corrupt Politician", "2026-02-17", "PT11M54S", 340756, 9461, 678, "Crime & Underworld"),
            ("K8WUcFAylxg", "How It Feels to Be in Every US Military Branch", "2026-02-13", "PT11M8S", 99812, 2565, 247, "Ranks & Hierarchy"),
            ("pCx7JBiXCJU", "What It Was Like to be Every Peaky Blinder Rank", "2026-02-10", "PT11M1S", 367641, 8303, 208, "Ranks & Hierarchy"),
            ("0n5xG4epnY0", "What It Was Like to be Every Roman Army Rank", "2026-02-04", "PT19M12S", 817484, 14728, 546, "Ranks & Hierarchy"),
            ("S9LXiTUygos", "What It Was Like to be Every Pirate Rank", "2026-01-31", "PT13M34S", 572490, 10557, 432, "Ranks & Hierarchy"),
            ("yQlup2BIMZA", "What It Was Like to be Every Samurai Rank", "2026-01-28", "PT15M39S", 942689, 19088, 511, "Ranks & Hierarchy"),
            ("EvuEMhh7SSk", "What It's Like to be a Dark Web Kingpin", "2026-01-09", "PT11M3S", 700953, 20317, 658, "Crime & Underworld"),
            ("_mV6X5Fbpys", "What It's Like to be Every Yakuza Rank", "2026-01-06", "PT11M43S", 1770164, 35003, 982, "Ranks & Hierarchy"),
            ("uMX5PwxqHWs", "POV: You're an International Arms Dealer", "2025-12-22", "PT11M1S", 779556, 24154, 601, "Crime & Underworld"),
            ("24VpqQN2gfY", "Your Life as Every Rank in the Italian Mafia", "2025-12-15", "PT10M29S", 2766186, 53847, 1868, "Ranks & Hierarchy"),
            ("ZXE0oK5WKvE", "Your Life as a Ruthless Hedge Fund CEO", "2025-12-11", "PT8M10S", 498883, 15029, 724, "Wealth & Money"),
            ("kz1AQHltnbQ", "POV: You're a Cartel Accountant", "2025-12-01", "PT11M50S", 1486628, 43058, 1299, "Crime & Underworld"),
            ("x92kaI7phzs", "What It's Like To Be Every CIA Rank", "2025-11-17", "PT17M12S", 331958, 8465, 351, "Ranks & Hierarchy"),
            ("5IdPdw62oT0", "Your Life as Every Position in the Cartel", "2025-11-01", "PT12M11S", 799270, 21251, 721, "Ranks & Hierarchy"),
            ("K4TJhugKWUk", "Good Debt Explained Like You're 5", "2025-10-19", "PT8M23S", 39306, 1282, 26, "Wealth & Money"),
            ("BVyJL_tcMd8", "How It Felt to be a Millionaire in Every Era", "2025-10-05", "PT14M37S", 243675, 5182, 235, "Wealth & Money"),
            ("UchQEgBmp0M", "What Every Level of Wealth ACTUALLY Feels Like", "2025-08-15", "PT15M36S", 1684422, 35957, 3447, "Wealth & Money"),
            ("Y_f1mqXTV6g", "Every Tax Loophole Used By Billionaires Explained in 9 Minutes", "2025-05-16", "PT9M2S", 200194, 7284, 195, "Wealth & Money"),
            ("p-axnDbMGKw", "Every Old Money Family Dynasty Explained in 10 Minutes", "2025-05-15", "PT10M33S", 461215, 10332, 365, "Wealth & Money"),
            ("zNtRUKeTcdM", "Every Type of Billionaire Explained in 10 Minutes", "2025-05-12", "PT10M2S", 39311, 1310, 48, "Wealth & Money"),
        ],
    },
    "wallace": {
        "channel": {
            "channelId": "UCWMmoNQsNKlXC5KofNO2w_g",
            "handle": "@WallaceAnimation",
            "title": "Wallace",
            "createdAt": "2024-11-11",
            "topics": ["Entertainment", "Film"],
            "subscribers": 206000,
            "totalViews": 31225688,
            "totalVideos": 34,
            "subsGained30d": 11000,
            "viewsGained30d": 3679505,
            "videosPublished30d": 2,
        },
        "videos": [
            ("W-nkxGUVbKM", "How You Would Die in Every Fallout Vault 2", "2026-06-10", "PT31M29S", 95918, 1900, 86, "Gaming Worlds"),
            ("tNc8OpsneVc", "The ENTIRE History of Vought", "2026-05-28", "PT20M50S", 881170, 16726, 534, "Superheroes & The Boys"),
            ("PaOGKtDWgp4", "How Every Member of The Seven Died", "2026-05-19", "PT17M44S", 1418793, 27206, 768, "Superheroes & The Boys"),
            ("IpTOVMG9h8Y", "How You Would Die on Every Invincible Planet", "2026-05-01", "PT14M52S", 218551, 4099, 181, "Superheroes & The Boys"),
            ("n6c6jvYlI9M", "Your Life as Every Viltrumite Rank", "2026-04-22", "PT16M55S", 2351209, 37528, 771, "Superheroes & The Boys"),
            ("j3ZtT95o324", "Your Life As a Clone Trooper", "2026-04-17", "PT18M39S", 233293, 5233, 210, "Star Wars"),
            ("1Az-7xhdtX8", "The ENTIRE History of the Viltrumite Empire", "2026-04-04", "PT14M6S", 408281, 8888, 450, "Superheroes & The Boys"),
            ("gQXgZ6po_0U", "Why It Sucks To Be a Star Wars Inquisitor", "2026-02-25", "PT15M57S", 288014, 8707, 347, "Star Wars"),
            ("ouQyoC-2wwU", "Why It Sucks to Be Born in Oz", "2026-02-12", "PT16M33S", 75108, 2761, 194, "Fantasy & Myth"),
            ("9aIx7TztkgE", "Why It Sucks To Be a Mandalorian", "2026-02-05", "PT20M45S", 298483, 6891, 296, "Star Wars"),
            ("rcbOR9UvPz4", "Your Life in the Warhammer 40K Imperial Guard", "2026-01-27", "PT22M29S", 308282, 7167, 455, "Gaming Worlds"),
            ("jFxbPlTs_LU", "Your Life As a Dragon Ball Saiyan", "2026-01-15", "PT20M24S", 248389, 7124, 515, "Fantasy & Myth"),
            ("Yzc2334kEVo", "Why It Sucks To Be a Na'vi", "2026-01-08", "PT17M49S", 373789, 11896, 683, "Fantasy & Myth"),
            ("UiP1X2z1gZc", "Why It Sucks To Be a Fallout Survivor", "2025-12-23", "PT19M31S", 339040, 7124, 274, "Gaming Worlds"),
            ("UvoLa4d0z0s", "How You Would Die in Every Fallout Vault", "2025-12-15", "PT22M42S", 2398535, 41230, 1128, "Gaming Worlds"),
            ("twfy7SEL_kU", "Why It Sucks To Be an Airbender", "2025-12-07", "PT19M41S", 512615, 12223, 682, "Fantasy & Myth"),
            ("2eFu-eqTg2s", "Why It Sucks To Be a Speedster", "2025-11-27", "PT15M21S", 592602, 14718, 838, "Superheroes & The Boys"),
            ("Hccp6fRnEtc", "Why It Sucks To Be a Witcher", "2025-11-19", "PT22M52S", 1302039, 40388, 1428, "Fantasy & Myth"),
            ("QbJfdJw4lec", "How You Would Die on Every Marvel Planet", "2025-11-11", "PT22M54S", 174097, 4027, 186, "Superheroes & The Boys"),
            ("XQ5Tw2hCxR4", "Why It Sucks To Be a Wizard", "2025-11-04", "PT18M20S", 575462, 17490, 1276, "Fantasy & Myth"),
            ("abSp8gTzfSI", "Why It Sucks to Be Born on Asgard", "2025-10-10", "PT18M23S", 324928, 8426, 303, "Superheroes & The Boys"),
            ("8HQLIHbL8qw", "Why It Sucks To Be a Stormtrooper", "2025-09-30", "PT20M3S", 815649, 19646, 747, "Star Wars"),
            ("bU_Ens69XnM", "Why It Sucks To Be a Halo Spartan", "2025-08-13", "PT19M35S", 3996499, 57356, 1823, "Gaming Worlds"),
            ("PQRfPVSaAGo", "Why It Sucks To Be a Sith Lord", "2025-07-12", "PT21M39S", 1782886, 45251, 2065, "Star Wars"),
            ("5I5gsMWTl5I", "Why It Sucks To Be a Werewolf", "2025-07-01", "PT21M20S", 527376, 15636, 1054, "Fantasy & Myth"),
            ("tWamU4Z-trs", "Why It Sucks To Be a Green Lantern", "2025-06-03", "PT18M", 1599425, 42371, 1340, "Superheroes & The Boys"),
            ("hqclXDLXbTs", "Why It Sucks To Be a Hobbit", "2025-05-27", "PT14M42S", 209624, 6088, 390, "Fantasy & Myth"),
            ("qqE4BJ4n_AQ", "How You Would Die on Every Star Wars Planet", "2025-05-16", "PT22M6S", 878820, 19803, 1086, "Star Wars"),
            ("rsk85FCtdcw", "Why It Sucks To Be a Vampire", "2025-05-08", "PT17M51S", 1179786, 34454, 2527, "Fantasy & Myth"),
            ("VQreg7AN6K4", "Why It Sucks to Be Born as a Mutant", "2025-04-05", "PT13M50S", 878969, 23203, 1026, "Superheroes & The Boys"),
            ("n-6ZfK6fei4", "Why It Sucks To Be a Jedi", "2025-03-15", "PT11M23S", 926333, 28351, 1118, "Star Wars"),
            ("3MHXq6ioG5Y", "Why It Sucks to Be Born as a Kryptonian", "2025-02-25", "PT8M59S", 587982, 16743, 631, "Superheroes & The Boys"),
            ("klU0-ZoEi0k", "Why It Sucks to Be Born as a Viltrumite", "2025-02-13", "PT15M58S", 4045656, 111239, 3527, "Superheroes & The Boys"),
            ("5kIwmU8rT3c", "Why It Sucks to Be Born on Arrakis", "2025-01-03", "PT8M35S", 400930, 9444, 255, "Fantasy & Myth"),
        ],
    },
    "odd_dude_explained": {
        "channel": {
            "channelId": "UC7Ol7s_cwU3oiBpeK8mfWww",
            "handle": "@OddDudeExplained",
            "title": "Odd Dude Explained",
            "createdAt": "2025-05-08",
            "topics": ["Society", "Film", "Entertainment"],
            "subscribers": 41200,
            "totalViews": 2986419,
            "totalVideos": 30,
            "subsGained30d": 1300,
            "viewsGained30d": 162164,
            "videosPublished30d": 0,
        },
        "videos": [
            ("uCChGJ8osWY", "POV: You're the Mechanic Who Builds the Cartels' Deadly Narco Tanks", "2026-03-13", "PT16M20S", 124307, 3603, 156, "Cartel & Drug World"),
            ("o49fpXGhhOg", "POV: Your Life as Every Rank of the Deadly MS-13 Gang", "2026-03-08", "PT20M40S", 85673, 1996, 120, "Crime & Power"),
            ("yaugglQRTQI", "POV: You're the Deadliest Yakuza Assassin in Tokyo's Underworld", "2026-03-04", "PT25M30S", 136712, 3095, 142, "Assassins & Hitmen"),
            ("nDzJUki3Gh8", "POV: You're the Wife of the Most Feared Drug Lord in the World", "2026-02-26", "PT19M50S", 15782, 557, 70, "Cartel & Drug World"),
            ("su7kHtdcW54", "POV: You Reincarnate As The World's Deadliest Assassin Over And Over Again (FULL)", "2026-02-23", "PT47M25S", 51896, 1402, 53, "Assassins & Hitmen"),
            ("GGtMDwsFZAg", "POV: You're the Most Wanted Criminal Hunted by Police and Cartels (FULL)", "2026-02-22", "PT51M57S", 66049, 1373, 115, "Crime & Power"),
            ("tqoYD1xaUCA", "POV: You Are a Boxer BOUGHT by a Cartel boss", "2026-02-21", "PT27M9S", 115692, 2634, 127, "Cartel & Drug World"),
            ("sY_b-Rjwcz8", "9 Levels in Boxing: Which One Are You?", "2026-02-19", "PT8M57S", 9484, 336, 27, "Levels Quiz"),
            ("WiZl8iGVf6U", "POV: You're a Criminal Laundering Money for Cartels and Outsmarting the FBI", "2026-02-17", "PT18M39S", 36475, 1114, 89, "Cartel & Drug World"),
            ("hCCcSqrlyY8", "12 Levels Inside a Powerful Dynasty: Which One Are You?", "2026-02-15", "PT10M18S", 9512, 345, 53, "Levels Quiz"),
            ("WAYZis5FOwc", "POV: You Are The Patriarch Behind The Most Feared Cartels", "2026-02-13", "PT19M9S", 34188, 1205, 132, "Cartel & Drug World"),
            ("YXP5ljtQrno", "POV: You are a Politician HUNTED by the Most Dangerous Cartel", "2026-02-10", "PT29M57S", 34797, 1359, 143, "Cartel & Drug World"),
            ("ii8JyMwUTTw", "The 7 Levels of Hitmen: Which One Are You?", "2026-02-08", "PT8M43S", 39537, 1153, 83, "Levels Quiz"),
            ("rBc5959TMnA", "POV: You Are The Assassin King Trapped in a Time Loop (Part 2)", "2026-02-07", "PT29M29S", 28141, 1019, 131, "Assassins & Hitmen"),
            ("ksWwnEbY9tc", "POV: You Are The Body Disposer for the World's Deadliest Cartel", "2026-02-04", "PT23M53S", 88287, 3140, 293, "Cartel & Drug World"),
            ("czzt0eWiqa0", "POV: You Are The Assassin King Trapped in a Time Loop (Part 1)", "2026-02-02", "PT18M35S", 34552, 1198, 123, "Assassins & Hitmen"),
            ("dSYoEGgrDhs", "POV: You Escape the World's Most Dangerous Prison", "2026-02-01", "PT7M35S", 22716, 812, 160, "Crime & Power"),
            ("f1PskgE2yQQ", "POV: You Are The Cartel's Deadliest Hitman", "2026-01-31", "PT27M13S", 655850, 19810, 868, "Assassins & Hitmen"),
            ("Z9JsmPt99ok", "POV: You are the PRESIDENT of a Country Ruled by CARTELS", "2026-01-30", "PT10M59S", 22168, 747, 105, "Crime & Power"),
            ("mGkh3lx5KHM", "POV: You Are an Anti Narcotics Customs Officer", "2026-01-29", "PT22M56S", 50983, 1523, 169, "Cartel & Drug World"),
            ("w7Q3XjoTUUE", "POV: You're the World's Most Wanted Arms Dealer", "2026-01-27", "PT17M55S", 78883, 2715, 225, "Crime & Power"),
            ("T4WaCJ8Uqsk", "POV: You Are a HACKER", "2026-01-26", "PT20M31S", 180047, 5453, 379, "Crime & Power"),
            ("lByOFEYh7ag", "POV: You Are the Son of a Politician", "2026-01-25", "PT24M31S", 54128, 2022, 191, "Crime & Power"),
            ("dzXAA3g8OsE", "POV: You Are a DEA Agent Infiltrating the Cartel", "2026-01-24", "PT19M39S", 61829, 1952, 147, "Cartel & Drug World"),
            ("VfqPdkzNSaI", "POV: You Are the MOST CRUEL Dictator in History", "2026-01-19", "PT14M8S", 41162, 1491, 146, "Crime & Power"),
            ("1t0pQg5yfDg", "POV: You are the GENIUS COOK for the Biggest DRUG LORD", "2026-01-17", "PT14M47S", 64844, 1998, 125, "Cartel & Drug World"),
            ("FJfDvMwPSMg", "POV: You're the Lawyer of the Most Wanted Drug Lord", "2026-01-16", "PT25M45S", 245990, 8859, 568, "Cartel & Drug World"),
            ("KGJACk3aTSI", "POV: You Are a Mob Boss", "2026-01-13", "PT14M54S", 84834, 2143, 103, "Crime & Power"),
            ("4Jy-UnaaX6Y", "POV: You Become a Drug Cartel Boss", "2026-01-11", "PT15M45S", 419466, 11257, 426, "Cartel & Drug World"),
            ("-BdGy9x2YWc", "POV: You Are the Son of a Cartel Boss", "2026-01-10", "PT16M19S", 98410, 3921, 177, "Cartel & Drug World"),
        ],
    },
}


def dur_to_sec(iso):
    m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", iso)
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)


def days_since(d):
    return (CAPTURE - date.fromisoformat(d)).days


def build(slug, raw):
    ch = raw["channel"]
    age = days_since(ch["createdAt"])
    raw_views = [v[4] for v in raw["videos"]]
    median_views = statistics.median(raw_views)

    videos = []
    for vid, title, pub, dur, views, likes, comments, topic in raw["videos"]:
        secs = dur_to_sec(dur)
        vage = max(days_since(pub), 1)
        eng = (likes + comments) / views if views else 0
        videos.append({
            "videoId": vid,
            "title": title,
            "publishedAt": pub,
            "ageDays": vage,
            "topic": topic,
            "durationSeconds": secs,
            "durationMin": round(secs / 60, 1),
            "titleHasNumber": bool(re.search(r"\d", title)),
            "titleWordCount": len(title.split()),
            "views": views,
            "likes": likes,
            "comments": comments,
            "engagementRate": round(eng * 100, 2),
            "likeRate": round(likes / views * 100, 2) if views else 0,
            "commentRate": round(comments / views * 100, 3) if views else 0,
            "viewsPerDay": round(views / vage),
            "outlierMultiple": round(views / median_views, 2) if median_views else 0,
        })

    # topic aggregates
    topics = {}
    for v in videos:
        t = topics.setdefault(v["topic"], {"topic": v["topic"], "count": 0, "totalViews": 0})
        t["count"] += 1
        t["totalViews"] += v["views"]
    for t in topics.values():
        t["avgViews"] = round(t["totalViews"] / t["count"])
    topic_aggs = sorted(topics.values(), key=lambda x: -x["avgViews"])

    total_views_sum = sum(raw_views)
    top3 = sum(sorted(raw_views, reverse=True)[:3])

    channel = {
        "slug": slug,
        "channelId": ch["channelId"],
        "handle": ch["handle"],
        "title": ch["title"],
        "createdAt": ch["createdAt"],
        "channelAgeDays": age,
        "topics": ch["topics"],
        "subscribers": ch["subscribers"],
        "totalViews": ch["totalViews"],
        "totalVideos": ch["totalVideos"],
        "avgViewsPerVideo": round(ch["totalViews"] / ch["totalVideos"]),
        "viewsPerSubscriber": round(ch["totalViews"] / ch["subscribers"], 1),
        "uploadsPerMonth": round(ch["totalVideos"] / (age / 30), 2),
        "subsGained30d": ch["subsGained30d"],
        "viewsGained30d": ch["viewsGained30d"],
        "videosPublished30d": ch["videosPublished30d"],
        "capturedAt": CAPTURE.isoformat(),
        "aggregates": {
            "medianViews": round(median_views),
            "medianEngagement": round(statistics.median(v["engagementRate"] for v in videos), 2),
            "medianViewsPerDay": round(statistics.median(v["viewsPerDay"] for v in videos)),
            "top3ViewSharePct": round(top3 / total_views_sum * 100, 1),
            "topicAggregates": topic_aggs,
        },
        "videos": videos,
    }
    return channel


def main():
    os.makedirs(os.path.join(OUTDIR, "channels"), exist_ok=True)
    index = []
    for slug, raw in RAW_CHANNELS.items():
        data = build(slug, raw)
        path = os.path.join(OUTDIR, "channels", f"{slug}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        index.append({
            "slug": slug,
            "title": data["title"],
            "handle": data["handle"],
            "subscribers": data["subscribers"],
            "totalVideos": data["totalVideos"],
        })
        print(f"wrote {path}  ({len(data['videos'])} videos)")
    with open(os.path.join(OUTDIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    print(f"wrote index.json  ({len(index)} channel(s))")


if __name__ == "__main__":
    main()
