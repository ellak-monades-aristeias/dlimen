import configparser


class Config:

    def __init__(self, fpath, interpolation=0):
        self.fpath = fpath
        self.configr = configparser.ConfigParser()
        if interpolation != 0:
            self.configr._interpolation = configparser.\
                ExtendedInterpolation()

    # ===========================================================================
    # reads the config file
    # ===========================================================================
    def get(self):
        return self.configr.read(self.fpath)

	# ===========================================================================
    # return the value of an option
    # ===========================================================================
    def get_option(self, section, option):
        return self.configr.get(section, option)
		
	# ===========================================================================
    # check if section exists, and create/set
    # an option
    # ===========================================================================
    def set(self, section, option, value):
        sections = self.get_sections()
        if section not in sections:
            self.configr.add_section(section)
        self.configr.set(section, option, value)

    # ===========================================================================
    # write changes to the actual config file
    #
    # used to create new config file, or to
    # write the changes after having used the set
    # function
    # ===========================================================================
    def write(self):
        try:
            config_file = open(self.fpath, 'w')
            self.configr.write(config_file)
            return 0  # OK
        except:
            return 1  # FAIL