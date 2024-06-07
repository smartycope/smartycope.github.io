import jstyleson as jsonc
# import json
from os.path import dirname, join; DIR  = dirname(__file__)
import argparse
from collections import OrderedDict

# -- Note: consider changing the scoring in the program to be added logirithmically, so the closer it comes to 100 the more it's actually worth, but still judged the same way.
# -- Also, maybe if they negatively fulfill the value half the negative

parser = argparse.ArgumentParser(description='Objectifying love!\nA helpful algorithm that tells you if you\'re overthinking things or not.')
parser.add_argument('preferencesFile', help='The preferences json file')
parser.add_argument('--outputFile', '-o', help='The name of the save file to use', nargs=1)
parser.add_argument('--inputFile', '-i', help='Input from a JSON file instead of manually', nargs=1)
parser.add_argument('--generate', '-g', help='Generate a new preferences file from another preferences file', nargs=1)
parser.add_argument('--suite', '--all', '-a', help='Generate a new preferences file from another specified preferences file, and then run the main algorithm with the new preferences file (do it all, basicallly)', nargs=1)
args = parser.parse_args()

DEFAULT_SAVES_PATH = DIR
PARTLY_VALUE = 0.6
ROUND_TO = 1

YES_SYNONYMS = 'y ya yeah yes si true definitely accurate'.split()
NO_SYNONYMS = ('n', 'no', 'not', 'nien', 'false', 'nope', 'not really')
NA_SYNONYMS = ('none', 'na', 'n/a', 'not applicable', 'idk', "don't know", 'dont know')
PARTLY_SYNONYMS = ('sure', 'kinda', 'i guess', 'kind of', 'maybe', 'ish', 'sorta', 'sort of')
UNDO_SYNONYMS = ('undo', 'go back', 'back')

def invertDict(d):
    """ Returns the dict given, but with the keys as values and the values as keys. """
    return dict(zip(d.values(), d.keys()))

def constrain(val, low, high):
    """ Constrains val to be within low and high """
    return min(high, max(low, val))

def getInput(trait):
    _input = input(trait.capitalize() + ': ').strip().lower().removesuffix('%')
    if _input in YES_SYNONYMS:
        return 1
    elif _input in NO_SYNONYMS:
        return 0
    elif _input in NA_SYNONYMS:
        return 'na'
    elif _input in PARTLY_SYNONYMS:
        return PARTLY_VALUE
    elif _input in UNDO_SYNONYMS:
        return None
    else:
        try:
            mod = float(_input)
            # If it's bigger than 1, assume it's a percentage
            if abs(mod) > 1 and abs(mod) <= 100:
                return mod / 100
            # If it's smaller than or equal to 1, assume it's a decimal
            if abs(mod) <= 1:
                return mod
            else:
                raise TypeError()
        except:
            print("Invalid input")
            return getInput(trait)

def applyTolerance(amt, tolerances):
    # This has to be in order
    for tolerance in sorted(tolerances.values(), reverse=True):
        if amt >= tolerance:
            return invertDict(tolerances)[tolerance]
    raise UserWarning("You've somehow scored less than is possible.")

def invertResponse(response):
    if response in YES_SYNONYMS or response == 1:
        return 'yes'
    elif type(response) in (int, float):
        return f'{response*100}%'
    elif response in NO_SYNONYMS:
        return 'no'
    elif response in NA_SYNONYMS:
        return 'n/a'
    elif response in PARTLY_SYNONYMS:
        return 'maybe'
    else:
        return response

def getWeightInput(trait, constraint):
    _input = input(f"How important to you is it that {trait.lower()}: ").strip().lower()
    if _input in NA_SYNONYMS:
        return 'na'
    elif _input in UNDO_SYNONYMS:
        return None
    else:
        try:
            return constrain(int(_input), (-constraint)-1, constraint+1)
        except:
            print("Invalid input")
            return getWeightInput(trait, constraint)

def getToleranceInput(relationship):
    _input = input(f'How perfectly does someone have to fit the criteria for you {relationship} them? (0.0-1.0): ').strip().lower().removesuffix('%')
    if _input in UNDO_SYNONYMS:
        return None
    else:
        try:
            mod = float(_input)
            # If it's bigger than 1, assume it's a percentage
            if abs(mod) > 1 and abs(mod) <= 100:
                return mod / 100
            # If it's smaller than or equal to 1, assume it's a decimal
            if abs(mod) <= 1:
                return mod
            else:
                raise TypeError()
        except:
            print("Invalid input")
            return getToleranceInput(trait)

def getSettingsInput(prompt):
    try:
        return float(input(prompt).strip().lower())
    except:
        print("Invalid input")
        return getSettingsInput(prompt)

def getTolerances(tolerances):
    rtn = {}
    for relationship, _ in tolerances.items():
        rtn[relationship] = getToleranceInput(relationship)
    return rtn

def getSettings():
    return {
        'constraint': getSettingsInput(f"What's magnitude of the scale we're using? (i.e. 100 for -100 to 100): "),
        'max dating unknowns': getSettingsInput(f"What's maximum amount of things you're not allowed to know about someone in order to date them?: "),
        'max marriage unknowns': getSettingsInput(f"What's maximum amount of things you're not allowed to know about someone in order to marry them?: "),
        'dealbreaker limit': getSettingsInput(f"How much do they have to fufull a dealbreaker before it's a dealbreaker?\n"
                                               "(i.e. They have to answer above this value on a dealbreaker question for it to count as a dealbreaker) (0.0-1.0): ")
    }

def printResults(person, max, count, unknowns, tolerances):
    print(f'\nOut of the {count} traits evaluated, they scored {round(person / count, ROUND_TO)} out of {round(max / count, ROUND_TO)} possible. That\'s {round((person / max) * 100, ROUND_TO)}%.')
    if unknowns:
        print(f'You didn\'t know {unknowns} things about them.')

    # Figure out if they've failed the max unknowns test or not
    relationship = applyTolerance(person / max, tolerances)
    if relationship == 'befriend':
        print('They would make a good friend')
    else:
        if relationship == 'date'  and unknowns > settings["max dating unknowns"] or \
            relationship == 'marry' and unknowns > settings["max marriage unknowns"]:
            print(f'They\'ll be good to {relationship} eventually, but you need to get to know them more first. Give it more time.')
        else:
            print(f'They are good to {relationship}.')

def generate(outFile):
    with open(args.preferencesFile, 'r') as f:
        tolerances, traits, settings = jsonc.load(f)
        traits = OrderedDict(traits)

    answers = OrderedDict()

    # First get tolerances and settings
    print("Tolerances:")
    tolerances = getTolerances(tolerances)
    print()
    print('Settings:')
    settings = getSettings()
    print()
    print('Traits:')
    print('Answer with numbers between the scale you just set, answers above and below the scale are treated as dealbreakers.')
    print("0 means it doesn't matter to you, and n/a means it doesn't apply to you")

    try:
        while len(traits):
            # We don't care what weight is already in the file
            trait, _ = traits.popitem()
            modifier = getWeightInput(trait, settings['constraint'])

            # Go back a question
            if modifier is None:
                # Add our current question back into the questions dict
                traits[trait] = 0
                if not len(answers):
                    continue
                # Then add the previous question into the questions dict
                key, val = answers.popitem()
                traits[key] = val
            elif modifier == 'na':
                continue
            else:
                answers[trait] = modifier

    finally:
        with open(outFile, 'w') as f:
            jsonc.dump([tolerances, answers, settings], f, indent=4)

def inputFile():
    # Open the file
    with open(args.preferencesFile, 'r') as f:
        tolerances, traits, settings = jsonc.load(f)
        tolerances["leave be"] = -1
        traits = OrderedDict(traits)

    with open(args.inputFile[0], 'r') as f:
        answers = jsonc.load(f)

    # First get their name so we can make a file for them
    person = 0
    max = 0
    count = 0
    unknowns = 0
    from Cope import debug
    for trait, weight in traits.items():
        # debug(answers)
        try:
            modifier = answers[trait]
        except KeyError:
            pass
        else:
            if modifier == 'na':
                unknowns += 1
            else:
                # If they've failed a dealbreaker question
                if  weight >  settings["constraint"] and modifier <      settings["dealbreaker limit"] or \
                    weight < -settings["constraint"] and modifier > (1 - settings["dealbreaker limit"]):
                    print(f'They failed a dealbreaker answering {invertResponse(modifier)} to {trait}.')
                    exit(0)
                else:
                    person += modifier * weight
                    max    += weight
                    count  += 1

    printResults(person, max, count, unknowns, tolerances)

def manualInput(preferencesFile):
    # Open the file
    with open(preferencesFile, 'r') as f:
        tolerances, traits, settings = jsonc.load(f)
        tolerances# Open the file

    # First get their name so we can make a file for them
    name = input('What is their name: ')
    person = 0
    max = 0
    count = 0
    unknowns = 0
    answers = OrderedDict()
    answered = OrderedDict()

    try:
        # for trait, weight in traits.items():
        while len(traits):
            trait, weight = traits.popitem()
            modifier = getInput(trait)

            # Go back a question
            if modifier is None:
                # Add our current question back into the questions dict
                traits[trait] = weight
                if not len(answered):
                    continue
                # Then add the previous question into the questions dict
                key, val = answered.popitem()
                traits[key] = val
            else:
                answers[trait] = modifier
                answered[trait] = weight

                # If they answer na, just move on
                if modifier == 'na':
                    unknowns += 1
                else:
                    # If they've failed a dealbreaker question
                    if  weight >  settings["constraint"] and modifier <      settings["dealbreaker limit"] or \
                        weight < -settings["constraint"] and modifier > (1 - settings["dealbreaker limit"]):
                        print('Stop now, that\'s a dealbreaker.')
                        # We still want to save what we have, but then end.
                        raise Exception()
                    else:
                        person += modifier * weight
                        max    += weight
                        count  += 1

        printResults(person, max, count, unknowns, tolerances)

    # Make sure we save the file at the end, even if we're inturrupted
    finally:
        with open(join(args.outputFile if args.outputFile else DEFAULT_SAVES_PATH, f'{name}sAttributes.json'), 'w+') as savefile:
            jsonc.dump(answers, savefile, indent=4)
            # savefile.write('\n'.join(answers))


if args.suite:
    print('First, calibrate the algorithm to what your personal preferences:')
    generate(args.suite[0])
    print()
    print('Now evaluate a specific person given the preferences you just set: ')
    manualInput(args.suite[0])
elif args.generate:
    generate(args.generate[0])
    print(f'Done! Your relationship preferences file is written at "{args.generate[1]}".')
elif args.inputFile:
    inputFile()
else:
    manualInput(args.preferencesFile)
