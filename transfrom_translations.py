from collections import Counter
import os
import polib
import sys

class Separator(object):
    def __init__(self, get_directory, save_directory="collected",get_po=None):
        self.get_directory = get_directory
        self.save_directory = save_directory
        self.over_po = None
        if get_po:
            self.over_po = get_po

        self.npoed_add = None
        self.npoed_add_js = None
        self.npoed_override = None
        self.npoed_override_js = None

    def save(self):
        if any(map(lambda x: x is None, [
            self.npoed_add,
            self.npoed_override,
            self.npoed_add_js,
            self.npoed_override_js
        ])):
            raise RuntimeError("Run .separate before save. (for {})".format(self.get_directory))
        self.npoed_add.save(self.save_directory + "/" + "npoed_add_" +self.get_directory +".po")
        self.npoed_add_js.save(self.save_directory + "/" + "npoed_add_" +self.get_directory +"js.po")

        self.npoed_override.save(self.save_directory + "/" + "npoed_over_" +self.get_directory +".po")
        self.npoed_override_js.save(self.save_directory + "/" + "npoed_over_" +self.get_directory +"js.po")

    def separate(self):
        self.npoed_add, self.npoed_override = self.process_js_or_py("py")
        self.npoed_add_js, self.npoed_override_js = self.process_js_or_py("js")
    
    def process_js_or_py(self, potype):
        pofiles_dir = self.get_directory + "/" + potype+"/"
        files = os.listdir(pofiles_dir)
        try:
            npoed_po, edx_po = self.over_po(files, pofiles_dir)
        except (RuntimeError, TypeError) as e:
            npoed_po, edx_po = self.get_po(files, pofiles_dir)

        npoed_add, npoed_override, stats = self.process_pair(npoed_po, edx_po)
        
        print(self.get_directory + "," + potype + ": add: {}; over: {}; passed: {}".format(*stats))
        return npoed_add, npoed_override

    def get_po(self, files, pofiles_dir):
        if (len(files) != 2):
            raise("Must be 2 files, found {}:{}".format(
                str(len(files)),
                str(files)
                ))
        npoed_filename = [x for x in files if "npoed" in x][0]
        edx_filename = [x for x in files if "edx" in x][0]
        return polib.pofile(pofiles_dir + "/" + npoed_filename), polib.pofile(pofiles_dir + "/" + edx_filename)

    def process_pair(self, npoed, edx):
        npoed_add = polib.POFile()
        npoed_override = polib.POFile()

        add = 0
        override = 0
        passed = 0
        for entry in npoed:
            has_id_and_str = (len(entry.msgstr) and len(entry.msgid))
            if not has_id_and_str:
                passed += 1
                continue

            edx_entry = get_entry(edx, entry.msgid)
            if edx_entry:
                if edx_entry.msgstr != entry.msgstr:
                    npoed_override.append(entry)
                    override += 1
                else:
                    passed += 1
            else:
                npoed_add.append(entry)
                add += 1
        return npoed_add, npoed_override, (add, override, passed)


def get_entry(pofile, msgid):
    cand = [e for e in pofile if e.msgid == msgid]
    if len(cand):
        return cand[0]
    return None

def get_proctor_po(files, pofiles_dir):
        if (len(files) != 3):
            raise RuntimeError("Must be 3 files, found {}:{}".format(
                str(len(files)),
                str(files)
                ))
        npoed_total = polib.POFile()

        npoed_platform = polib.pofile(pofiles_dir + "npoed_platform.po")
        npoed_proctoring = polib.pofile(pofiles_dir + "npoed_proctoring.po")
        edx = polib.pofile(pofiles_dir + "edx_master.po")
        for entry in npoed_proctoring.translated_entries():
            if entry not in npoed_platform.translated_entries():
                npoed_total.append(entry)
            else:
                print("Proctoring conflict: {}".format(entry.msgid))
        return npoed_total, edx



def separate():    
    ora_sep = Separator("ora2")
    ora_sep.separate()
    ora_sep.save() 

    platform_sep = Separator("platform")
    platform_sep.separate()
    platform_sep.save()

    proctor_sep = Separator("proctoring", get_po=get_proctor_po)
    proctor_sep.separate()
    proctor_sep.save()

    npoed_total = polib.POFile()
    npoed_total.extend(platform_sep.npoed_add)
    npoed_total.extend(platform_sep.npoed_override)
    
def compile(directory="collected/"):
    files = os.listdir(directory)
    is_js_file = lambda x: ("js" in x)
    files = [f for f in files if not("total" in f)]

    files_js = [f for f in files if is_js_file(f)]
    files_py = [f for f in files if not is_js_file(f)]

    npoed_py = polib.POFile()
    print("Compiling py .po files...")
    po_objs_py = dict((f,polib.pofile(directory + f)) for f in files_py)
    for f, p in po_objs_py.items():
        print("\t{}:{}".format(f, len(p)))
        npoed_py.extend(p)

    npoed_js = polib.POFile()
    print("Compiling js .po files...")
    po_objs_js = dict((f,polib.pofile(directory + f)) for f in files_js)
    for f, p in po_objs_js.items():
        print("\t{}:{}".format(f, len(p)))
        npoed_js.extend(p)
    
    npoed_py.save(directory + "npoed_total.po")
    npoed_js.save(directory + "npoed_totaljs.po")
    fuzzy_py = [key for key,val in Counter([m.msgid for m in npoed_py]).items() if val>1]
    fuzzy_js = [key for key,val in Counter([m.msgid for m in npoed_js]).items() if val>1]

    fuzzy_mes = "Fuzzy 'msgid's! They must be solved before using in edx"
    if fuzzy_py or fuzzy_js:
        print("="*len(fuzzy_mes))
        print(fuzzy_mes)
    if fuzzy_py:
        print("In py({}):".format(len(fuzzy_py)))
    for key in fuzzy_py:
        print("msgid {}".format(key))
        for f,p in po_objs_py.items():
            found_entry = get_entry(p, key)
            if found_entry:
                print("\t {} : {}".format(f, found_entry.msgstr))

    if fuzzy_js:
        print("In js({}):".format(len(fuzzy_js)))
    
    for key in fuzzy_js:
        print("msgid {}".format(key))
        for f,p in po_objs_js.items():
            found_entry = get_entry(p, key)
            if found_entry:
                print("\t {} : {}".format(f, found_entry.msgstr))
    print("="*len(fuzzy_mes))
    print("Total: py {}, js {}".format(
        len(npoed_py),
        len(npoed_js)
        )
    )

if __name__ == "__main__":
    err = ValueError("You must give 1 arg: 'separate' or 'compile'")
    if len(sys.argv) < 2:
        raise err
    if sys.argv[1] == "separate":
        separate()
    elif sys.argv[1] == "compile":
        compile()
    else:
        raise err