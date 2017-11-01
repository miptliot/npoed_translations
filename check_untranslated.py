import polib
import os


def check_untranslated(untranslated_addr):
    npoed_total = polib.pofile("collected/npoed_total.po")
    npoed_totaljs = polib.pofile("collected/npoed_totaljs.po")
    untranslated = polib.pofile(untranslated_addr)
    all_entries_are_untranslated = True
    for entry in untranslated:
        npoed_entry = npoed_total.find(entry.msgid) 
        if npoed_entry:
            all_entries_are_untranslated = False
            print("\t" +unicode(npoed_entry))
        
        npoed_entryjs = npoed_totaljs.find(entry.msgid) 
        if npoed_entryjs:
            all_entries_are_untranslated = False
            print("\t" +unicode(npoed_entryjs))
    return all_entries_are_untranslated  

if __name__ == "__main__":
    directory = "edx_untranslated/"
    filenames = os.listdir(directory)
    for f in filenames:
        print("Checking {}...".format(f))
        check = check_untranslated(directory + f)
        if check:
            print("All untranslated")
        else: 
            print("We already have translations for those entries")
