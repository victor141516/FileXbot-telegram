class Explorer(object):

    def __init__(self, telegram_id, db, files_per_page):
        super(Explorer, self).__init__()
        self.db = db
        self.user = self.db.select('users', "telegram_id = " + str(telegram_id))[0]
        self.path = [self.db.select(
            'directories', "name = '/' AND parent_directory_id is NULL AND user_id = " + str(self.user['id']))[0]['id']]
        self.last_action_message_ids = []
        self.files_per_page = files_per_page
        self.explorer_list_position = 0
        self.explorer_list_size = 0
        self.last_sent_file = None

    def get_current_dir(self):
        cur_dir_id = self.path[-1]
        return self.db.select('directories', "id = " + str(cur_dir_id))[0]

    def get_path_string(self):
        try:
            return '/' + ('/'.join([
                self.db.select('directories', "id = " + str(directory))[0]['name']
                for directory in self.path[1:]
            ]))
        except Exception as e:
            print(e)
            return "Error getting path"

    def get_directory_content(self, directory_id=None):
        if (len(self.path) == 0):
            self.__init__(self.user['telegram_id'])
        if (not directory_id):
            directory_id = self.path[-1:][0]
        try:
            str(int(directory_id))
        except Exception as e:
            return False

        directories = self.db.select('directories', "parent_directory_id = " +
                                     str(directory_id))

        shares = self.db._selectRaw('''SELECT 'shares' as type, shares.*, directories.name
                                    FROM shares
                                    JOIN directories ON directories.id = shares.directory_id
                                    WHERE shares.user_id = {0}
                                    AND shares.parent_directory_id = {1}'''.format(str(self.user['id']), str(directory_id)))

        directories = sorted(directories + shares, key=lambda x: x['name'].lower())

        files = self.db.select('files', "directory_id = " +
                               str(directory_id))
        files = sorted(files, key=lambda x: x['name'].lower())

        elements = directories + files
        self.explorer_list_size = len(elements)
        elements = elements[self.explorer_list_position * self.files_per_page:   (
            self.explorer_list_position+1) * self.files_per_page]

        return elements

    def go_to_directory(self, directory_id):
        try:
            str(int(directory_id))
        except Exception as e:
            return False
        directory_id = self.db.select(
            'directories', "id = " + directory_id)[0]['id']
        self.path.append(directory_id)
        self.explorer_list_position = 0

    def go_to_parent_directory(self):
        if (len(self.path) == 0):
            self.__init__(self.user['telegram_id'])
        self.path = self.path[:-1]
        self.explorer_list_position = 0

    def new_directory(self, directory_name, parent_directory_id=None):
        if (not parent_directory_id):
            parent_directory_id = self.path[-1:][0]
        return self.db.insert('directories', {'name': directory_name.replace("'", "").replace('"', ""), 'parent_directory_id': parent_directory_id, 'user_id': self.user['id']})

    def new_file(self, telegram_id, name, mime, size, directory_id=None):
        if (not directory_id):
            directory_id = self.path[-1:][0]
        return self.db.insert('files', {'name': name.replace("'", "").replace('"', ""), 'mime': mime, 'size': size, 'telegram_id': telegram_id, 'directory_id': directory_id, 'user_id': self.user['id']})

    def receive_share(self, directory_id, parent_directory_id=None):
        if (parent_directory_id == None):
            parent_directory_id = self.get_current_dir()['id']

        user = self.db.select('users', "id = " + str(self.user['id']))
        if (len(user) == 0):
            return False

        user = user[0]

        return self.db.insert('shares', {
            'user_id': user['id'],
            'directory_id': directory_id,
            'parent_directory_id': parent_directory_id,
        })

    def remove_shares(self, deleting_user_id=False, directory_ids=False):
        if (not directory_ids):
            directory_ids = [self.get_current_dir()['id']]

        directory_ids_string = ', '.join(
            [(str(int(each))) for each in directory_ids])

        if (deleting_user_id):
            deleting_user_id = str(int(deleting_user_id))
            return self.db.delete('shares', "directory_id = (" + directory_ids_string + ") AND user_id = " + deleting_user_id)
        else:
            return self.db.delete('shares', "directory_id in (" + directory_ids_string + ")")

    def remove_files(self, file_ids):
        if (len(file_ids) == 0):
            return True
        try:
            file_ids_string = ', '.join(
                [(str(int(each))) for each in file_ids])
        except Exception as e:
            return False
        return self.db.delete('files', "id in (" + file_ids_string + ")")

    def remove_directories(self, directory_ids):
        if (len(directory_ids) == 0):
            return True
        try:
            directory_ids_string = ', '.join(
                [(str(int(each))) for each in directory_ids])
        except Exception as e:
            return False

        for directory_id in directory_ids:
            content = self.get_directory_content(directory_id)
            self.remove_files(list(filter(lambda a: a['type'] != "files", content)))
            self.remove_directories(list(filter(lambda a: a['type'] != "directories", content)))
        return self.db.delete('directories', "id in (" + directory_ids_string + ")")
