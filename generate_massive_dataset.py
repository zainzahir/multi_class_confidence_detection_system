import csv
import os
import random

def generate_dataset():
    # Parts of speech for High Confidence (English)
    high_subjects = [
        "I am", "We are", "The team is", "My analysis shows I am", "I feel", "I am definitely",
        "I absolutely feel", "I am fully", "I have completely", "I can easily", "I have clearly",
        "I am 100% sure I am", "Undoubtedly, I am"
    ]
    high_adverbs = [
        "absolutely", "completely", "perfectly", "100%", "definitely", "fully", "totally",
        "entirely", "extremely", "thoroughly", "confidently", "undoubtedly", "clearly",
        "genuinely", "certainly"
    ]
    high_adjectives = [
        "certain", "sure", "confident", "positive", "clear", "accurate", "secure", "correct",
        "satisfied", "prepared", "competent", "knowledgeable", "adept", "expert", "clear-headed",
        "on track"
    ]
    high_clauses = [
        "about this solution", "that this is correct", "of my answer", "with this approach",
        "about the topic", "on this test", "regarding this concept", "about the code logic",
        "with this calculation", "on this homework", "concerning this subject", "about my performance",
        "with this solution set"
    ]
    high_followups = [
        "and can explain it clearly", "and there is no doubt", "because it is easy",
        "without any hesitation", "and I can teach others", "and I verified it twice",
        "after reviewing the notes", "as the logic is solid", "because I studied hard",
        "and it makes perfect sense", "as the logic is flawless", "and the results prove it",
        "without any second thought"
    ]

    # Parts of speech for Medium Confidence (English)
    med_subjects = [
        "I think", "I believe", "Maybe", "Probably", "It seems", "I guess", "I suppose",
        "I suspect", "I assume", "It looks like", "Probably I am", "I guess I might be",
        "I'm under the impression"
    ]
    med_verbs = [
        "might be", "is likely", "could be", "is probably", "should be", "looks",
        "seems to be", "appears", "could potentially be", "is likely to be"
    ]
    med_adjectives = [
        "correct", "right", "fine", "ok", "accurate", "reasonable", "acceptable",
        "satisfactory", "plausible", "decent", "passable"
    ]
    med_clauses = [
        "but I need to check", "though I have some doubts", "but I'm not 100% sure",
        "but I want to verify", "but there are gaps in my knowledge", "though I need to review",
        "but let me double-check", "but I should double check", "although I need some review",
        "but I have some minor hesitation", "though I want to verify the details"
    ]
    med_followups = [
        "in my notes", "with the textbook", "before finalizing", "with my teacher",
        "with my classmates", "later tonight", "just in case", "before submitting it",
        "with the class reference", "against the answers key"
    ]

    # Parts of speech for Low Confidence (English)
    low_subjects = [
        "I am", "I feel", "I have", "The student is", "I became", "I am totally",
        "I feel completely", "I've got", "The problem is I am", "I am completely and utterly"
    ]
    low_adverbs = [
        "completely", "totally", "extremely", "really", "deeply", "utterly", "severely",
        "dreadfully", "hopelessly"
    ]
    low_adjectives = [
        "confused", "lost", "uncertain", "doubtful", "clueless", "struggling", "blank",
        "perplexed", "frustrated", "overwhelmed", "stuck", "puzzled", "befuddled", "disoriented"
    ]
    low_clauses = [
        "about this topic", "on this question", "what the answer is", "how to solve this",
        "what is going on here", "with this basic concept", "about this difficult formula",
        "regarding this method", "on this assignment", "with this math equation", "on this coding block"
    ]
    low_followups = [
        "and I need help", "because it is too hard", "and it makes no sense", "and I want guidance",
        "and I need clarification", "and I am failing to understand", "so I am guessing the answer",
        "and I don't know what to do", "since it is way too complicated", "and I need someone to explain it",
        "and it is very frustrating"
    ]

    # Roman Urdu components
    roman_high = [
        ("mujhe poora yakeen hai ye sahi hai", "High Confidence"),
        ("ye bilkul sahi answer hai", "High Confidence"),
        ("maine saare steps sahi kiye hain", "High Confidence"),
        ("concept bilkul clear hai mujhe", "High Confidence"),
        ("mujhe is topic par poori grip hai", "High Confidence"),
        ("bilkul sahi samajh aayi hai mujhe", "High Confidence"),
        ("easy tha main araam se kar sakta hoon", "High Confidence"),
        ("koi doubt nahi hai mujhe isme", "High Confidence"),
        ("meri understanding bilkul perfect hai", "High Confidence"),
        ("bina kisi shak ke ye sahi hai", "High Confidence"),
        ("main isey doosron ko bhi samjha sakta hoon", "High Confidence"),
        ("haji bilkul 100% sahi hai", "High Confidence"),
        ("mujhe bilkul confirm pata hai", "High Confidence"),
        ("maine ache se samjha hai ye topic", "High Confidence"),
        ("main confirm hoon ye answer right hai", "High Confidence"),
        ("mje pura yakeen h is pr", "High Confidence"),
        ("bhai ye 100 percent correct answer hai", "High Confidence"),
        ("sare concepts fit hain mere", "High Confidence"),
        ("tension nahi hai, bilkul sahi kiya hai", "High Confidence"),
        ("answer perfect hai main check kar chuka hoon", "High Confidence"),
        ("mje bilkul clear h sub kuch", "High Confidence"),
        ("100% sure hoon main is baar", "High Confidence"),
        ("ye to boht easy question tha, ho gaya", "High Confidence"),
        ("concept full clear hai, koi doubt nahi", "High Confidence"),
        ("yes, absolute correct answer hai ye", "High Confidence"),
        ("maine verify kar liya hai book se, yehi hai", "High Confidence"),
        ("easy task tha, main ne solve kar liya", "High Confidence"),
        ("i am fully confident ye sahi hai", "High Confidence"),
        ("tension free, ye answer bilkul right hai", "High Confidence"),
        ("meray sare concepts crystal clear hain", "High Confidence"),
        ("no doubts at all, ready for test", "High Confidence"),
        ("perfectly understood, ready for next topic", "High Confidence"),
        ("bina kisi hesitation ke ye correct answer hai", "High Confidence"),
        ("is subject pr meri command boht achi hai", "High Confidence"),
        ("ye to 2 mins ka kaam tha, solve ho gaya", "High Confidence"),
        ("correct result hai, main proof kar sakta hoon", "High Confidence"),
        ("poora test easily solve ho jayega", "High Confidence"),
        ("i know this topic very well", "High Confidence"),
        ("absolutely right concept hai ye", "High Confidence"),
        ("mujhe poora bharosa hai apne solution par", "High Confidence"),
        ("perfect, koi galti nahi hai isme", "High Confidence"),
        ("full marks aenge is test me guaranteed", "High Confidence"),
        ("concept solid hai mera is chapter ka", "High Confidence"),
        ("mai bina kisi book k ye samjha sakta hu", "High Confidence"),
        ("ye solution 100% tested aur verified hai", "High Confidence"),
        ("no confusion, output clear hai", "High Confidence"),
        ("mje full confirm h iska", "High Confidence"),
        ("bhai bilkul confirm he ye answer", "High Confidence"),
        ("easy peasy, fully prepared hoon", "High Confidence"),
        ("is topic me meri mastery hai", "High Confidence"),
        ("surely correct, checked twice", "High Confidence"),
        ("maine saari derivations khud solve ki hain", "High Confidence"),
        ("concept crystal clear, doubts clear", "High Confidence"),
        ("i am fully satisfied with my solution", "High Confidence"),
        ("mere saare doubts clear ho chuke hain", "High Confidence"),
        ("ye correct hai aur isme koi doubt nahi hai", "High Confidence"),
        ("easy task tha main araam se kar lya", "High Confidence"),
        ("i solved it without any help", "High Confidence"),
        ("i understand this fully and have no questions", "High Confidence"),
        ("ye solution 100% correct hai, match kar lo", "High Confidence"),
        ("bilkul confirm hai, isme koi issue nahi", "High Confidence"),
        ("mujhe complete commands hain is per", "High Confidence"),
        ("ye to mera favorite topic hai, clear he", "High Confidence"),
        ("maine iski boht practice ki hai", "High Confidence"),
        ("easily done, no doubt about it", "High Confidence"),
        ("i can easily explain the logic", "High Confidence"),
        ("mujhe poora confidence hai is answer pe", "High Confidence"),
        ("poora concept clear he sir", "High Confidence"),
        ("maine code run kiya aur correct output aya", "High Confidence"),
        ("perfect, exact matching output aya hai", "High Confidence"),
        ("highly confident about this result", "High Confidence"),
        ("everything is fully clear to me", "High Confidence"),
        ("main 100% sure hoon is calculation par", "High Confidence"),
        ("maine har step double check kiya hai", "High Confidence"),
        ("easy to understand context hai ye", "High Confidence"),
        ("yes i got this, 100% sure", "High Confidence"),
        ("concept ok hai full confidence hai", "High Confidence"),
        ("sure answer hai, match ho gaya", "High Confidence"),
        ("perfectly done by me", "High Confidence"),
        ("yes sure answer is correct", "High Confidence")
    ]

    roman_med = [
        ("mujhe thoda boht samajh aaya hai", "Medium Confidence"),
        ("shayad ye sahi hai par check karna parega", "Medium Confidence"),
        ("thodi confusion hai lekin sahi lag raha hai", "Medium Confidence"),
        ("kuch concepts samajh aaye hain kuch nahi", "Medium Confidence"),
        ("main confirm nahi hoon lekin shayad sahi ho", "Medium Confidence"),
        ("mujhe thoda aur practice ki zaroorat hai", "Medium Confidence"),
        ("concepts thode clear hain lekin poore nahi", "Medium Confidence"),
        ("kuch cheezein bhol rahi hain mujhe", "Medium Confidence"),
        ("maybe ye sahi ho par confirm nahi", "Medium Confidence"),
        ("koshish ki hai par poora yakeen nahi hai", "Medium Confidence"),
        ("thoda mushkil laga par samajh aa gaya thoda", "Medium Confidence"),
        ("aadha samajh aaya hai aadha nahi", "Medium Confidence"),
        ("kuch points clear hain aur kuch me doubt hai", "Medium Confidence"),
        ("mujhse thodi galti ho sakti hai isme", "Medium Confidence"),
        ("check karna parega par lagta hai thik hai", "Medium Confidence"),
        ("lagta to thik hai par senior se poochna parega", "Medium Confidence"),
        ("half understanding hai meri abhi tak", "Medium Confidence"),
        ("kuch cheezein aati hain kuch bhol jati hain", "Medium Confidence"),
        ("umeed to hai sahi hoga par guarantee nahi", "Medium Confidence"),
        ("baki sab thik hai bas aakhri step me thoda doubt hai", "Medium Confidence"),
        ("shayad ye sahi ho sakta hai, confirm nahi", "Medium Confidence"),
        ("mere khyal se option b sahi hai par check karna hoga", "Medium Confidence"),
        ("kuch points clear hain but full detail nahi aati", "Medium Confidence"),
        ("i think ye sahi hai, but check kr lena", "Medium Confidence"),
        ("maybe this is right, but not 100% sure", "Medium Confidence"),
        ("thoda mushkil tha but maine try kiya hai", "Medium Confidence"),
        ("aadha concept samajh aya hai, aadha baki hai", "Medium Confidence"),
        ("50-50 chance hai ke ye correct ho", "Medium Confidence"),
        ("concept to thik hai par calculation check krni paray gi", "Medium Confidence"),
        ("lagta to thik hai par test cases check karne parain ge", "Medium Confidence"),
        ("i have some idea about this topic but need review", "Medium Confidence"),
        ("mostly clear hai but complex questions nahi hote", "Medium Confidence"),
        ("ummed hai thik hoga, main sure nahi hoon", "Medium Confidence"),
        ("kuch confusion hai concepts me", "Medium Confidence"),
        ("mje lagta h ye sahi h pr guarantee ni", "Medium Confidence"),
        ("concept simple lag raha hai par sure nahi", "Medium Confidence"),
        ("mostly correct hai, bas thoda sa doubt hai", "Medium Confidence"),
        ("class me samajh aya tha par ab thoda bhol raha hai", "Medium Confidence"),
        ("mujhe lagta hai maine formula thik lagaya hai", "Medium Confidence"),
        ("try kiya hai, umeed hai sahi hoga", "Medium Confidence"),
        ("concept samajh aa raha hai thoda thoda", "Medium Confidence"),
        ("maybe i need to revise this once more", "Medium Confidence"),
        ("formula thik lag raha hai par calculations verify karni hain", "Medium Confidence"),
        ("mje 100 percent confirm ni h pr shyd yehi ho", "Medium Confidence"),
        ("mujhe 70% sure he ke yehi answer he", "Medium Confidence"),
        ("ek baar cross check karna parega", "Medium Confidence"),
        ("concept aatha hai par solve karne me thodi problem hai", "Medium Confidence"),
        ("kuch basic ideas clear hain bas details miss ho rhi hain", "Medium Confidence"),
        ("i think i am close to the solution", "Medium Confidence"),
        ("not fully sure, but seems correct", "Medium Confidence"),
        ("maybe yes, but i need clarification", "Medium Confidence"),
        ("thoda sa doubt hai answer pr", "Medium Confidence"),
        ("main bilkul sure nahi hoon par check kar leta hoon", "Medium Confidence"),
        ("almost correct lag raha he", "Medium Confidence"),
        ("koshish to achi thi par aakhri step complex tha", "Medium Confidence"),
        ("aaj class me thoda samajh aya tha", "Medium Confidence"),
        ("i think answer is correct but verify karna parega", "Medium Confidence"),
        ("half formula yaad hai, half bhol gaya", "Medium Confidence"),
        ("i guess this works but need to test", "Medium Confidence"),
        ("maybe option a or b me se koi aik hai", "Medium Confidence"),
        ("lag to raha he thik he, dekhte hain", "Medium Confidence"),
        ("concept thoda fuzzy hai abhi", "Medium Confidence"),
        ("50% sure hoon main is calculation par", "Medium Confidence"),
        ("i believe it is right, hope so", "Medium Confidence"),
        ("mje thoda confirm krna parega notes se", "Medium Confidence"),
        ("mere concepts okay hain par practice kam he", "Medium Confidence"),
        ("mostly true but minor errors possible", "Medium Confidence"),
        ("mujhe lagta hai maine isey sahi handle kiya hai", "Medium Confidence"),
        ("i guess i am on the right track", "Medium Confidence"),
        ("not perfectly sure, let me double check", "Medium Confidence"),
        ("kuch formulas confusing hain baki thik he", "Medium Confidence"),
        ("i think ye work karega but test krna hoga", "Medium Confidence"),
        ("almost sure, 90% sure about it", "Medium Confidence"),
        ("concept clear h but solution m confusion h", "Medium Confidence"),
        ("check kr k btaunga, abi half clear h", "Medium Confidence"),
        ("maybe correct, let me know if it is wrong", "Medium Confidence"),
        ("concept is okay but some parts are hard", "Medium Confidence"),
        ("i am mostly sure, just a little doubt", "Medium Confidence"),
        ("it looks correct but need peer review", "Medium Confidence"),
        ("hope ye sahi ho, main verify karunga", "Medium Confidence")
    ]

    roman_low = [
        ("mujhe bilkul samajh nahi aaya", "Low Confidence"),
        ("boht mushkil hai ye topic mere liye", "Low Confidence"),
        ("mujhe kuch bhi samajh nahi aa raha", "Low Confidence"),
        ("mujhe boht confusion ho rahi hai", "Low Confidence"),
        ("main completely blank hoon isme", "Low Confidence"),
        ("mujhse ye nahi ho raha boht tough hai", "Low Confidence"),
        ("meri samajh se bahar hai ye sab", "Low Confidence"),
        ("help chahiye mujhe kuch samajh nahi aa raha", "Low Confidence"),
        ("koi concept clear nahi hai mera isme", "Low Confidence"),
        ("mujhe bilkul yakeen nahi hai apne answer par", "Low Confidence"),
        ("sab sir ke oopar se guzar gaya", "Low Confidence"),
        ("zero samajh aayi hai mujhe", "Low Confidence"),
        ("mujhe is topic par boht doubt hai kuch samajh nahi aya", "Low Confidence"),
        ("boht mushkil lag raha hai ye question", "Low Confidence"),
        ("bilkul palle nahi para ye concept", "Low Confidence"),
        ("mje kuch ni pata iska kia answer h", "Low Confidence"),
        ("sir g boht mushkil kaam hai ye", "Low Confidence"),
        ("zero knowledge hai meri is topic pr", "Low Confidence"),
        ("dimagh ghoom gaya hai is sawal pr", "Low Confidence"),
        ("kuch samajh nahi aya bilkul sir ke upar se gaya", "Low Confidence"),
        ("mujhse bilkul nahi ho raha ye", "Low Confidence"),
        ("concept sir ke oopar se guzar gaya", "Low Confidence"),
        ("boht hi mushkil question hai, blank hoon main", "Low Confidence"),
        ("completely confused, help chahiye", "Low Confidence"),
        ("mujhe bilkul samajh nahi aa raha ye topic", "Low Confidence"),
        ("i have zero knowledge about this", "Low Confidence"),
        ("pata nahi kya chal raha hai is code me", "Low Confidence"),
        ("help me, main bilkul blank hoon", "Low Confidence"),
        ("mje kuch smjh ni a rha kia kron", "Low Confidence"),
        ("everything is going over my head", "Low Confidence"),
        ("i am failing to understand this concept", "Low Confidence"),
        ("boht hi tough hai, mujhse nahi hoga", "Low Confidence"),
        ("completely lost on this question", "Low Confidence"),
        ("no idea how to solve this equation", "Low Confidence"),
        ("mujhe to kuch yaad hi nahi aa raha", "Low Confidence"),
        ("sir g boht mushkil lag raha hai ye", "Low Confidence"),
        ("totally clueless about this chapter", "Low Confidence"),
        ("meri to tayari bilkul zero hai", "Low Confidence"),
        ("maths ke formula samajh nahi aate", "Low Confidence"),
        ("dimagh ka dahi ho gaya hai is topic pr", "Low Confidence"),
        ("please help, mujhse ye solve nahi ho raha", "Low Confidence"),
        ("i don't understand anything in this lecture", "Low Confidence"),
        ("completely stuck on the first step", "Low Confidence"),
        ("ye coding mere bas ki baat nahi hai", "Low Confidence"),
        ("mujhe kuch bhi recall nahi ho raha", "Low Confidence"),
        ("zero understanding, zero confidence", "Low Confidence"),
        ("mje math se dar lagta he", "Low Confidence"),
        ("completely confused, nothing is clear", "Low Confidence"),
        ("boht hi ganda concept he ye, samajh ni aya", "Low Confidence"),
        ("meray sar me dard ho rha h is topic se", "Low Confidence"),
        ("please explain this from scratch, i am lost", "Low Confidence"),
        ("clueless about what the teacher is saying", "Low Confidence"),
        ("totally blank, no ideas at all", "Low Confidence"),
        ("i failed to solve this even after trying twice", "Low Confidence"),
        ("mujhe to lagta he ye boht heavy level maths he", "Low Confidence"),
        ("nothing makes sense to me in this code", "Low Confidence"),
        ("completely unconfident, i will fail", "Low Confidence"),
        ("mere bas ka kaam nahi hai ye software engineering", "Low Confidence"),
        ("i don't have any interest or understanding in this", "Low Confidence"),
        ("ye chapter boht zyada boring aur mushkil he", "Low Confidence"),
        ("i am failing to follow these instructions", "Low Confidence"),
        ("mujhe basic concepts bhi clear nahi hain", "Low Confidence"),
        ("pata nahi teacher kya padha rahe hain", "Low Confidence"),
        ("i am hopelessly stuck here", "Low Confidence"),
        ("mje guide kren mje bilkul ni pta iska", "Low Confidence"),
        ("i have no confidence on my skills", "Low Confidence"),
        ("this is way too difficult for a beginner like me", "Low Confidence"),
        ("totally confused about how to run this script", "Low Confidence"),
        ("is question me kya karna hai mje pata nahi", "Low Confidence"),
        ("sab kuch sar ke upar se nikal gya", "Low Confidence"),
        ("highly confused and blank right now", "Low Confidence"),
        ("i have zero ideas to resolve this error", "Low Confidence"),
        ("boht bekaar concept he mje thora b samjh ni aya", "Low Confidence"),
        ("everything is a mess in my mind right now", "Low Confidence"),
        ("i can't understand these mathematical formulas", "Low Confidence"),
        ("mujhse ye solution nahi banega", "Low Confidence"),
        ("zero grip, completely lost", "Low Confidence"),
        ("i am totally overwhelmed by this topic", "Low Confidence"),
        ("please help me, i am clueless", "Low Confidence"),
        ("pata nahi iska answer kya hai, i am guessing", "Low Confidence")
    ]

    dataset = set()

    # Generate High Confidence (English)
    while len([d for d in dataset if d[1] == "High Confidence"]) < 500:
        sub = random.choice(high_subjects)
        adv = random.choice(high_adverbs)
        adj = random.choice(high_adjectives)
        cl = random.choice(high_clauses)
        fl = random.choice(high_followups)
        
        # Diversify templates
        pattern = random.randint(1, 3)
        if pattern == 1:
            sentence = f"{sub} {adv} {adj} {cl} {fl}."
        elif pattern == 2:
            sentence = f"{sub} {adj} {cl}."
        else:
            sentence = f"{adv.capitalize()} {adj}, {sub} sure {cl}."
            
        dataset.add((sentence, "High Confidence"))

    # Generate Medium Confidence (English)
    while len([d for d in dataset if d[1] == "Medium Confidence"]) < 500:
        sub = random.choice(med_subjects)
        verb = random.choice(med_verbs)
        adj = random.choice(med_adjectives)
        cl = random.choice(med_clauses)
        fl = random.choice(med_followups)
        
        pattern = random.randint(1, 3)
        if pattern == 1:
            sentence = f"{sub} this {verb} {adj} {cl} {fl}."
        elif pattern == 2:
            sentence = f"It {verb} {adj}, {cl}."
        else:
            sentence = f"{sub} it is {adj} {cl}."
            
        dataset.add((sentence, "Medium Confidence"))

    # Generate Low Confidence (English)
    while len([d for d in dataset if d[1] == "Low Confidence"]) < 500:
        sub = random.choice(low_subjects)
        adv = random.choice(low_adverbs)
        adj = random.choice(low_adjectives)
        cl = random.choice(low_clauses)
        fl = random.choice(low_followups)
        
        pattern = random.randint(1, 3)
        if pattern == 1:
            sentence = f"{sub} {adv} {adj} {cl} {fl}."
        elif pattern == 2:
            sentence = f"{sub} {adj} {cl}."
        else:
            sentence = f"I have no idea {cl}, it is {adv} {adj}."
            
        dataset.add((sentence, "Low Confidence"))

    # Add Roman Urdu data
    for text, label in (roman_high + roman_med + roman_low):
        dataset.add((text, label))

    # Convert to list and shuffle
    dataset_list = list(dataset)
    random.shuffle(dataset_list)

    # Write to dataset.csv
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(base_dir, 'dataset.csv')
    
    with open(dataset_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['text', 'confidence_level'])
        for text, label in dataset_list:
            writer.writerow([text, label])

    print(f"[SUCCESS] Generated massive dataset.csv with {len(dataset_list)} unique rows.")

if __name__ == '__main__':
    generate_dataset()
