#
# This is an extension to the Nautilus file manager to allow better 
# integration with the Subversion source control system.
# 
# Copyright (C) 2010 by Jason Heeris <jason.heeris@gmail.com>
# Copyright (C) 2008-2010 by Adam Plumb <adamplumb@gmail.com>
# 
# RabbitVCS is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# RabbitVCS is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with RabbitVCS;  If not, see <http://www.gnu.org/licenses/>.
#

import os.path

import gtk

import rabbitvcs.lib.helper

from rabbitvcs import gettext
_ = gettext.gettext

from rabbitvcs.lib.log import Log
log = Log("rabbitvcs.ui.contextmenuitems")
_ = gettext.gettext


SEPARATOR = u'\u2015' * 10

class MenuItem(object):
    """
    This is the base class for a definition of a menu item. Consider this
    "abstract" (in the language of Java) - it makes no sense to instantiate it
    directly. If you want to define a new kind of menu item, you need to
    subclass it like so:
    
    class MenuPerformMagic:
        identifier = "RabbitVCS::Perform_Magic"
        label = _("Perform Magic")
        tooltip = _("Put on your robe and wizard hat")
        icon = "rabbitvcs-wand" # or, say, gtk.STOCK_OPEN
    
    There is some introspection magic that goes on to associate the items
    themselves with certain methods of a ContextMenuCondition object or a
    ContextMenuCallback object. This is done by looking at the identifier - the
    part of the identifier after "::" is converted to lowercase and the item
    looks for a method of that name (eg. in the example above,
    "perform_magic").
    
    It is easy to override this, just define condition_name and callback_name
    to be what you need. If the item cannot find anything, it defaults to not
    assigning the callback and having the condition return False.
    
    There a few ways to organise this (and maybe it would be better to have the
    GtkContextMenu class do it), but this is it for the moment.
    """
    
    @staticmethod
    def default_condition(*args, **kwargs):
        return False
    
    @staticmethod
    def make_default_name(identifier):
        return identifier.split(MenuItem.IDENTIFIER_SEPARATOR)[-1].lower()
    
    IDENTIFIER_SEPARATOR = "::"
    
    # These are all explicitly defined here to make it obvious what a subclass
    # needs to set up.
    
    # This is relevant for GTK and Nautilus - they require unique identifiers
    # for all the elements of their menus. Make sure it starts with
    # "RabbitVCS::"
    identifier = None
    
    # The label that appears on the menu item. It is up to the subclass to
    # designate it as translatable.
    label = None
    
    # The tooltip for the menu item. It is up to the subclass to designate it as
    # translatable.
    tooltip = ""
    
    # The icon that will appear on the menu item. This can be, say,
    # "rabbitvcs-something" or gtk.STOCK_SOMETHING
    icon = None

    # This is a string that holds the name of the function that is called when
    # the menu item is activated (it is assigned to
    # self.signals["activate"]["callback"])
    #
    # The menu item will look for a callable attribute of this name in the
    # callback object passed in to the constructor. If it is None, it will try
    # to assign a default callback based on the identifier. If nothing is found
    # then no callback will be assigned to the "activate" signal.
    callback_name = None
    callback_args = ()


    # This is a string that holds the name of the function that is called to
    # determine whether to show the item.
    #
    # The menu item will look for a callable attribute of this name in the
    # callback object passed in to the constructor. If it is None, or False, or
    # it cannot find anything, it will set up a function that returns False.
    condition_name = None
    condition_args = ()
    
    def __init__(self, conditions, callbacks):
        """
        Creates a new menu item for constructing the GTK context menu.
        """
        
        self.signals = {}
        
        default_name = MenuItem.make_default_name(self.identifier)
        
        # These flags are used for sanity checks that developers can run to
        # ensure completeness of conditions and callbacks.
        # See contextmenu.TestMenuItemFunctions() 
        self.found_callback = False
        self.found_condition = False
        
        # If no callback name is set, assign the default
        if self.callback_name is None:
            # log.debug("Using default callback name: %s" % default_name)
            self.callback_name = default_name

        # Try to get the callback function for this item
        callback = self._get_function(callbacks, self.callback_name)


        if callback:
                self.signals["activate"] = {
                    "callback": callback,
                    "args": self.callback_args
                    }
                self.found_callback = True
#        else:
#            log.debug("Could not find callback for %s" % self.identifier)

        self.condition = {
            "callback": MenuItem.default_condition,
            "args": self.condition_args
            }            

        if self.condition_name is None:
            self.condition_name = default_name
            
        condition = self._get_function(conditions, self.condition_name)
        
        if condition:
            self.condition["callback"] = condition
            self.found_condition = True
#        else:
#            log.debug("Could not find condition for %s" % self.identifier)
    
    def show(self):
        return self.condition["callback"](*self.condition["args"])
    
    def _get_function(self, object, name):
        
        function = None
        
        if hasattr(object, name):
            
            attr = getattr(object, name)
            if callable(attr):
                function = attr
        
        return function
      
    def make_magic_id(self, id_magic = None):
        identifier = self.identifier
        
        if id_magic:
            identifier = identifier + "-" + str(id_magic)
            
        return identifier
      
    def make_action(self, id_magic = None):
        """
        Creates the GTK Action for the menu item. To avoid GTK "helpfully"
        preventing us from adding duplicates (eg. separators), you can pass in
        a string that will be appended and separated from the actual identifier.
        """
        identifier = self.make_magic_id(id_magic)
        return gtk.Action(identifier, self.label, None, None)

    def make_gtk_menu_item(self, id_magic = None):
        action = self.make_action(id_magic)
            
        if self.icon:
            # We use this instead of gtk.Action.set_icon_name because
            # that method is not available until pygtk 2.16
            action.set_menu_item_type(gtk.ImageMenuItem)
            menuitem = action.create_menu_item()
            menuitem.set_image(gtk.image_new_from_icon_name(self.icon, gtk.ICON_SIZE_MENU))
        else:
            menuitem = action.create_menu_item()
            
        return menuitem
    
    def make_nautilus_menu_item(self, id_magic = None):
        # WARNING: this import is here because it will fail if it is not done
        # inside a nautilus process and therefore can't be in the module proper.
        # I'm happy to let the exception propagate the rest of the time, since
        # this method shouldn't be called outside of nautilus.
        identifier = self.make_magic_id(id_magic)
        import nautilus
        menuitem = nautilus.MenuItem(
            identifier,
            self.label,
            self.tooltip,
            self.icon
        )
        
        return menuitem

    
class MenuDebug(MenuItem):
    identifier = "RabbitVCS::Debug"
    label = _("Debug")
    icon = "rabbitvcs-monkey"

class MenuBugs(MenuItem):
    identifier = "RabbitVCS::Bugs"
    label = _("Bugs")
    icon = "rabbitvcs-bug"

class MenuDebugShell(MenuItem):
    identifier = "RabbitVCS::Debug_Shell"
    label = _("Open Shell")
    icon = "gnome-terminal"
    condition_name = "debug" 

class MenuRefreshStatus(MenuItem):
    identifier = "RabbitVCS::Refresh_Status"
    label = _("Refresh Status")
    icon = "rabbitvcs-refresh"

class MenuDebugRevert(MenuItem):
    identifier = "RabbitVCS::Debug_Revert"
    label = _("Debug Revert")
    tooltip = _("Reverts everything it sees")
    icon = "rabbitvcs-revert"
    condition_name = "debug"

class MenuDebugInvalidate(MenuItem):
    identifier = "RabbitVCS::Debug_Invalidate"
    label = _("Invalidate")
    tooltip = _("Force an invalidate_extension_info() call")
    icon = "rabbitvcs-clear"
    condition_name = "debug"

class MenuDebugAddEmblem(MenuItem):
    identifier = "RabbitVCS::Debug_Add_Emblem"
    label = _("Add Emblem")
    tooltip = _("Add an emblem")
    icon = "rabbitvcs-emblems"
    condition_name = "debug"

class MenuCheckout(MenuItem):
    identifier = "RabbitVCS::Checkout"
    label = _("Checkout...")
    tooltip = _("Check out a working copy")
    icon = "rabbitvcs-checkout"
class MenuUpdate(MenuItem):
    identifier = "RabbitVCS::Update"
    label = _("Update")
    tooltip = _("Update a working copy")
    icon = "rabbitvcs-update"

class MenuCommit(MenuItem):
    identifier = "RabbitVCS::Commit"
    label = _("Commit")
    tooltip = _("Commit modifications to the repository")
    icon = "rabbitvcs-commit"

class MenuRabbitVCS(MenuItem):
    identifier = "RabbitVCS::RabbitVCS"
    label = _("RabbitVCS")
    icon = "rabbitvcs"

class MenuRepoBrowser(MenuItem):
    identifier = "RabbitVCS::Repo_Browser"
    label = _("Repository Browser")
    tooltip = _("Browse a repository tree")
    icon = gtk.STOCK_FIND

class MenuCheckForModifications(MenuItem):
    identifier = "RabbitVCS::Check_For_Modifications"
    label = _("Check for Modifications...")
    tooltip = _("Check for modifications made to the repository")
    icon = "rabbitvcs-checkmods"

class MenuDiffMenu(MenuItem):
    identifier = "RabbitVCS::Diff_Menu"
    label = _("Diff Menu...")
    tooltip = _("List of comparison options")
    icon = "rabbitvcs-diff"

class MenuDiff(MenuItem):
    identifier = "RabbitVCS::Diff"
    label = _("View diff against base")
    tooltip = _("View the modifications made to a file")
    icon = "rabbitvcs-diff"

class MenuDiffMultiple(MenuItem):
    identifier = "RabbitVCS::Diff_Multiple"
    label = _("View diff between files/folders")
    tooltip = _("View the differences between two files")
    icon = "rabbitvcs-diff"

class MenuDiffPrevRev(MenuItem):
    identifier = "RabbitVCS::Diff_Previous_Revision"
    label = _("View diff against previous revision")
    tooltip = _("View the modifications made to a file since its last change")
    icon = "rabbitvcs-diff"

class MenuCompareTool(MenuItem):
    identifier = "RabbitVCS::Compare_Tool"
    label = _("Compare with base")
    tooltip = _("Compare with base using side-by-side comparison tool")
    icon = "rabbitvcs-compare"

class MenuCompareToolMultiple(MenuItem):
    identifier = "RabbitVCS::Compare_Tool_Multiple"
    label = _("Compare files/folders")
    tooltip = _("Compare the differences between two items")
    icon = "rabbitvcs-compare"

class MenuCompareToolPrevRev(MenuItem):
    identifier = "RabbitVCS::Compare_Tool_Previous_Revision"
    label = _("Compare with previous revision")
    tooltip = _("Compare with previous revision using side-by-side comparison tool")
    icon = "rabbitvcs-compare"

class MenuShowChanges(MenuItem):
    identifier = "RabbitVCS::Show_Changes"
    label = _("Show Changes...")
    tooltip = _("Show changes between paths and revisions")
    icon = "rabbitvcs-changes"
    
class MenuShowLog(MenuItem):
    identifier = "RabbitVCS::Show_Log"
    label = _("Show Log")
    tooltip = _("Show a file's log information")
    icon = "rabbitvcs-show_log"

class MenuAdd(MenuItem):
    identifier = "RabbitVCS::Add"
    label = _("Add")
    tooltip = _("Schedule items to be added to the repository")
    icon = "rabbitvcs-add"

class MenuAddToIgnoreList(MenuItem):
    identifier = "RabbitVCS::Add_To_Ignore_List"
    label = _("Add to ignore list")
    icon = None

class MenuUpdateToRevision(MenuItem):
    identifier = "RabbitVCS::Update_To_Revision"
    label = _("Update to revision...")
    tooltip = _("Update a file to a specific revision")
    icon = "rabbitvcs-update"

class MenuRename(MenuItem):
    identifier = "RabbitVCS::Rename"
    label = _("Rename...")
    tooltip = _("Schedule an item to be renamed on the repository")
    icon = "rabbitvcs-rename"

class MenuDelete(MenuItem):
    identifier = "RabbitVCS::Delete"
    label = _("Delete")
    tooltip = _("Schedule an item to be deleted from the repository")
    icon = "rabbitvcs-delete"

class MenuRevert(MenuItem):
    identifier = "RabbitVCS::Revert"
    label = _("Revert")
    tooltip = _("Revert an item to its unmodified state")
    icon = "rabbitvcs-revert"

class MenuResolve(MenuItem):
    identifier = "RabbitVCS::Resolve"
    label = _("Resolve")
    tooltip = _("Mark a conflicted item as resolved")
    icon = "rabbitvcs-resolve"

class MenuRestore(MenuItem):
    identifier = "RabbitVCS::Restore"
    label = _("Restore")
    tooltip = _("Restore a missing item")

class MenuRelocate(MenuItem):
    identifier = "RabbitVCS::Relocate"
    label = _("Relocate...")
    tooltip = _("Relocate your working copy")
    icon = "rabbitvcs-relocate"

class MenuGetLock(MenuItem):
    identifier = "RabbitVCS::Get_Lock"
    label = _("Get Lock...")
    tooltip = _("Locally lock items")
    icon = "rabbitvcs-lock"

class MenuUnlock(MenuItem):
    identifier = "RabbitVCS::Unlock"
    label = _("Release Lock...")
    tooltip = _("Release lock on an item")
    icon = "rabbitvcs-unlock"

class MenuCleanup(MenuItem):
    identifier = "RabbitVCS::Cleanup"
    label = _("Cleanup")
    tooltip = _("Clean up working copy")
    icon = "rabbitvcs-cleanup"

class MenuExport(MenuItem):
    identifier = "RabbitVCS::Export"
    label = _("Export...")
    tooltip = _("Export a working copy or repository with no versioning information")
    icon = "rabbitvcs-export"

class MenuCreateRepository(MenuItem):
    identifier = "RabbitVCS::Create_Repository"
    label = _("Create Repository here")
    tooltip = _("Create a repository in a folder")
    icon = "rabbitvcs-run"

class MenuImport(MenuItem):
    identifier = "RabbitVCS::Import"
    label = _("Import")
    tooltip = _("Import an item into a repository")
    icon = "rabbitvcs-import"
    # "import" is reserved
    condition_name = "_import"
    callback_name = "_import"


class MenuBranchTag(MenuItem):
    identifier = "RabbitVCS::Branch_Tag"
    label = _("Branch/tag...")
    tooltip = _("Copy an item to another location in the repository")
    icon = "rabbitvcs-branch"

class MenuSwitch(MenuItem):
    identifier = "RabbitVCS::Switch"
    label = _("Switch...")
    tooltip = _("Change the repository location of a working copy")
    icon = "rabbitvcs-switch"

class MenuMerge(MenuItem):
    identifier = "RabbitVCS::Merge"
    label = _("Merge...")
    tooltip = _("A wizard with steps for merging")
    icon = "rabbitvcs-merge"

class MenuAnnotate(MenuItem):
    identifier = "RabbitVCS::Annotate"
    label = _("Annotate...")
    tooltip = _("Annotate a file")
    icon = "rabbitvcs-annotate"

class MenuCreatePatch(MenuItem):
    identifier = "RabbitVCS::Create_Patch"
    label = _("Create Patch...")
    tooltip = _("Creates a unified diff file with all changes you made")
    icon = "rabbitvcs-createpatch"

class MenuApplyPatch(MenuItem):
    identifier = "RabbitVCS::Apply_Patch"
    label = _("Apply Patch...")
    tooltip = _("Applies a unified diff file to the working copy")
    icon = "rabbitvcs-applypatch"

class MenuProperties(MenuItem):
    identifier = "RabbitVCS::Properties"
    label = _("Properties")
    tooltip = _("View the properties of an item")
    icon = "rabbitvcs-properties"

class MenuHelp(MenuItem):
    identifier = "RabbitVCS::Help"
    label = _("Help")
    tooltip = _("View help")
    icon = "rabbitvcs-help"

class MenuSettings(MenuItem):
    identifier = "RabbitVCS::Settings"
    label = _("Settings")
    tooltip = _("View or change RabbitVCS settings")
    icon = "rabbitvcs-settings"

class MenuAbout(MenuItem):
    identifier = "RabbitVCS::About"
    label = _("About")
    tooltip = _("About RabbitVCS")
    icon = "rabbitvcs-about"

class MenuOpen(MenuItem):
    identifier = "RabbitVCS::Open"
    label = _("Open")
    tooltip = _("Open a file")
    icon = gtk.STOCK_OPEN
    # Not sure why, but it was like this before...
    condition_name = "_open"
    callback_name = "_open"

class MenuBrowseTo(MenuItem):
    identifier = "RabbitVCS::Browse_To"
    label = _("Browse to")
    tooltip = _("Browse to a file or folder")
    icon = gtk.STOCK_HARDDISK

class MenuSeparator(MenuItem):
    identifier = "RabbitVCS::Separator"
    label = SEPARATOR
       
    def make_insensitive(self, menuitem):
        menuitem.set_property("sensitive", False)
       
    # Make separators insensitive
    def make_gtk_menu_item(self, id_magic = None):
        menuitem = super(MenuSeparator, self).make_gtk_menu_item(id_magic)
        self.make_insensitive(menuitem)
        return menuitem
    
    def make_nautilus_menu_item(self, id_magic = None):
        menuitem = super(MenuSeparator, self).make_nautilus_menu_item(id_magic)
        self.make_insensitive(menuitem)
        return menuitem

class PropMenuRevert(MenuItem):
    identifier = "RabbitVCS::Property_Revert"
    label = _("Revert property")
    icon =  "rabbitvcs-revert"
    tooltop = _("Revert this property to its original state")
    
class PropMenuRevertRecursive(MenuItem):
    identifier = "RabbitVCS::Property_Revert_Recursive"
    label = _("Revert property (recursive)")
    icon =  "rabbitvcs-revert"
    tooltop = _("Revert this property to its original state (recursive)")
    condition_name = "property_revert"
    callback_name = "property_revert"
    
class PropMenuDelete(MenuItem):
    identifier = "RabbitVCS::Property_Delete"
    label = _("Delete property")
    icon =  "rabbitvcs-delete"
    tooltop = _("Delete this property")
    
class PropMenuDeleteRecursive(MenuItem):
    identifier = "RabbitVCS::Property_Delete_Recursive"
    label = _("Delete property")
    icon =  "rabbitvcs-revert"
    tooltop = _("Delete this property (recursive)")
    condition_name = "property_delete"
    callback_name = "property_delete"

def get_ignore_list_items(paths):
    """
    Build up a list of items to ignore based on the selected paths

    @param  paths: The selected paths
    @type   paths: list

    """
    ignore_items = []
    
    # Used to weed out duplicate menu items
    added_ignore_labels = []
    
    # These are ignore-by-filename items
    ignorebyfilename_index = 0
    for path in paths:
        basename = os.path.basename(path)
        if basename not in added_ignore_labels:
            key = "IgnoreByFileName%s" % str(ignorebyfilename_index)
            
            class MenuIgnoreFilenameClass(MenuItem):
                identifier = "RabbitVCS::%s" % key
                label = basename
                tooltip = _("Ignore item by filename")
                callback_name = "ignore_by_filename"
                callback_args = (path)
                condition_name = "ignore_by_filename"
                condition_args = (path)
            
            ignore_items.append((MenuIgnoreFilenameClass, None))

    # These are ignore-by-extension items
    ignorebyfileext_index = 0
    for path in paths:
        extension = rabbitvcs.lib.helper.get_file_extension(path)
        
        ext_str = "*%s"%extension
        if ext_str not in added_ignore_labels:
            
            class MenuIgnoreFileExtClass(MenuItem):
                identifier = "RabbitVCS::%s" % key
                label = ext_str
                tooltip = _("Ignore item by file extension")
                callback_name = "ignore_by_file_extension"
                callback_args = (path, extension)
                condition_name = "ignore_by_file_extension"
                condition_args = (path, extension)
            
            ignore_items.append((MenuIgnoreFileExtClass, None))

    return ignore_items