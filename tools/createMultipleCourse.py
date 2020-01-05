#! /usr/bin/python
"""
Builds an additional (multiple) course to an existing jupyterhub+nbgrader installation

Also the following two variables must exist in the jupyterhub configuration file

    # c.JupyterHub.load_groups = {}
    # c.JupyterHub.services = []

usage: createMultipleCourse.py [-h] [--nbgrader_course_directory [COURSEDIR]]
                               [--jupyterhub_config_filename [CONFIG]]
                               [--jupyterhub_service_port [PORT]]
                               [--jupyterhub_api_token [TOKEN]]
                               [--nbgrader_course_header_include]
                               [--logging_level [LEVEL]]
                               [--nbgrader_students_filename [STUDENTSFILE] |
                               --create_all]
                               COURSE TEACHER

Create Nbgrader Course

positional arguments:
  COURSE                Nbgader course name
  TEACHER               Nbgrader teachers account name

optional arguments:
  -h, --help            show this help message and exit
  --nbgrader_course_directory [COURSEDIR], -d [COURSEDIR]
                        Path to nbgrader course directory root
  --jupyterhub_config_filename [CONFIG], -c [CONFIG]
                        Path to jupyterhub config filename
  --jupyterhub_service_port [PORT], -p [PORT]
                        Jupyterhub service port number
  --jupyterhub_api_token [TOKEN], -t [TOKEN]
                        Jupyterhub api_token
  --nbgrader_course_header_include, -i
                        Include nbgrader course header into course
  --logging_level [LEVEL], -l [LEVEL]
                        Logging level
  --nbgrader_students_filename [STUDENTSFILE], -s [STUDENTSFILE]
                        Nbgrader add students from students csv filename to
                        course
  --create_all, -a      Run createAll

"""

import os
import sys
import argparse
import subprocess
import tempfile
import logging
import nbformat
import csv

class createMultipleCourse():

    def __init__(self,**kwargs):
        mandatory = {'nbgrader_course_id',
                     'nbgrader_course_directory',
                     'nbgrader_teacher_account',
                     'nbgrader_students_filename',
                     'jupyterhub_service_port',
                     'jupyterhub_api_token',
                     'jupyterhub_config_filename',
                     'jupyter_bin_command',
                     'nbgrader_course_header_ipynb'}
        diff = mandatory-set(kwargs.keys())
        if len(diff):
            raise ValueError(f"missing argument(s) {diff}")
        else:
            self.__dict__.update(kwargs)

        #
        # Default template for adding groups and services to jupyterhub_config.py
        #
        # The following two variables must exist in jupyterhub_config.py
        #
        # c.JupyterHub.load_groups = {}
        # c.JupyterHub.services = []
        #

        self.jupyterhub_config_template = f"""
c.JupyterHub.load_groups.update({{
    'formgrade-{self.nbgrader_course_id}': [
        '{self.nbgrader_teacher_account}',
    ],
    'nbgrader-{self.nbgrader_course_id}': [],
   }}
)

c.Authenticator.admin_users.update({{'{self.nbgrader_teacher_account}'}})

c.JupyterHub.services.append(
    {{
        'name': '{self.nbgrader_course_id}',
        'url': 'http://127.0.0.1:{self.jupyterhub_service_port}/jupyter',
        'command': [
            'jupyterhub-singleuser',
            '--group=formgrade-{self.nbgrader_course_id}',
            '--debug',
        ],
        'user': '{self.nbgrader_teacher_account}',
        'cwd': '{self.nbgrader_course_directory}',
        'api_token': '{self.jupyterhub_api_token}'
    }}
)
"""

        #
        # Default template for nbgrader_config.py
        #

        self.nbgrader_config_template = f"""c = get_config()

c.CourseDirectory.root = '{self.nbgrader_course_directory}'
c.CourseDirectory.course_id = '{self.nbgrader_course_id}'
#c.IncludeHeaderFooter.header = 'source/header.ipynb'
"""

    def createAll(self):
        self.addGroupsServices2JHconfig()
        self.createCourseDirectory()
        if self.nbgrader_course_header_ipynb: self.includeHeader()
        self.createNBconfig()
        self.nbgraderExtensions("enable")

    def checkGroupsServicesInJHconfig(self):
        """
        Check for groups and services to jupyterhub_config.py
        """
        with open(self.jupyterhub_config_filename) as JHC:
            JHCcontent = JHC.read()
        indxGroup = JHCcontent.find("\nc.JupyterHub.load_groups")
        indxServices = JHCcontent.find("\nc.JupyterHub.services")
        if indxGroup == -1:
            raise ValueError("Groups (c.JupyterHub.load_groups) are not available in jupyterhub config file")
        if indxServices == -1:
            raise ValueError("Services (c.JupyterHub.services) are not available in jupyterhub config file")

    def addGroupsServices2JHconfig(self):
        """
        Add groups and services to jupyterhub_config.py
        """
        with open(self.jupyterhub_config_filename,"a") as JHC:
            JHC.write(self.jupyterhub_config_template)
            logging.debug(f"appended to {self.jupyterhub_config_filename}:\n{self.logging_separator}\n{self.jupyterhub_config_template}\n{self.logging_separator}") 

    def createCourseDirectory(self):
        """
        Create CourseDirectory.root if it does not exists
        """
        os.makedirs(self.nbgrader_course_directory, exist_ok=True)
        logging.debug(f"created (makedirs) {self.nbgrader_course_directory}\n{self.logging_separator}\n{self.logging_separator}") 


    def includeHeader(self):
        """
        Create source folder if it does not exist and create header.ipynb
        """ 
        os.makedirs(os.path.join(self.nbgrader_course_directory,"source"), exist_ok=True)
        logging.debug(f"created (makedirs) {self.nbgrader_course_directory}/source\n{self.logging_separator}\n{self.logging_separator}") 
        self.nbgrader_config_template.replace("#c.IncludeHeaderFooter.header = 'source/header.ipynb'","c.IncludeHeaderFooter.header = 'source/header.ipynb'")
        nbformat.write(self.nbgrader_course_header_ipynb,os.path.join(self.nbgrader_course_directory,"source","header.ipynb"))
        logging.debug(f"created {self.nbgrader_course_directory}/source/header.ipynb:\n{self.logging_separator}\n{nbformat.writes(self.nbgrader_course_header_ipynb)}\n{self.logging_separator}") 
        
    def createNBconfig(self):
        """
        Create nbgrader_config.py in CourseDirectory.root
        """
        with open(os.path.join(self.nbgrader_course_directory,"nbgrader_config.py"),"w") as NBC:
            NBC.write(self.nbgrader_config_template)
        logging.debug(f"created {self.nbgrader_course_directory}/nbgrader_config.py:\n{self.logging_separator}\n{self.nbgrader_config_template}\n{self.logging_separator}") 

    def nbgraderExtensions(self,what="enable"):
        """
        Enable or disable mandatory nbgrader extensions for teachers
        
        usage: nbgraderExtensions(what)
        
            parameter what(str) = "enable" | "disable"
        """
        
        if what in ["enable","disable"]:
            extensions = {"nbextension":["create_assignment/main",
                                         "course_list/main --section=tree"],
                          "serverextension":["nbgrader.server_extensions.formgrader",
                                             "nbgrader.server_extensions.course_list"]}
            for typ in extensions:
                for extension in extensions[typ]:
                    process = subprocess.run(["sudo","-u",self.nbgrader_teacher_account,"-i",self.jupyter_bin_command,typ,what,"--user"]+extension.split(" "), capture_output=True)
                    logging.debug(f"output returned:\n{self.logging_separator}\n{' '.join(process.args)}\n\n{process.stdout.decode()}\n\n{process.stderr.decode()}\n{self.logging_separator}")
        else:
            raise ValueError(f"wrong argument what={what} to nbgraderExtension(what) - what allows only 'enable' or 'disable'")

    def addStudents2Course(self):
        """
        Add students to course which are listed in a csv file where columns ['username','mail','givenName','sn'] are included
        """
        if self.nbgrader_students_filename:
            with open(self.nbgrader_students_filename, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                mandatory_columns = {'username','mail','givenName','sn'}
                diff = mandatory_columns-set(reader.fieldnames)
                if not len(diff):
                    cwd = os.getcwd()
                    os.chdir(self.nbgrader_course_directory)
                    for student in reader:
                        process = subprocess.run(["nbgrader","db","student","add",
                                                  f"--courseDirectory.course_id={self.nbgrader_course_id}",
                                                  f"{student['username']}",
                                                  f"--DbStudentAddApp.email={student['mail']}",
                                                  f"--DbStudentAddApp.first_name={student['givenName']}",
                                                  f"--DbStudentAddApp.last_name={student['sn']}",
                                                  f"--DbStudentAddApp.lms_user_id={student['username']}"], capture_output=True)
                        logging.debug(f"output returned:\n{self.logging_separator}\n{' '.join(process.args)}\n\n{process.stdout.decode()}\n\n{process.stderr.decode()}\n{self.logging_separator}") 
                    os.chdir(cwd)
                else:
                    raise ValueError(f"Mandatory columns ({mandatory_columns}) are not available in student file columns ({set(reader.fieldnames)})")
    
def parseArguments(jupyterhub_api_token,
                   jupyterhub_service_port_startnumbers=19,
                   nbgrader_course_directory_template='/home/TEACHER/Courses/COURSE/'):
    """
    Arguments to be parsed
    """
    
    logging_level = {'CRITICAL':50,'ERROR':40,'WARNING':30,'INFO':20,'DEBUG':10,'NOTSET':0}
    
    parser = argparse.ArgumentParser(description='Create Nbgrader Course')
    parser.add_argument('nbgrader_course_id', metavar='COURSE', type=str,
                        help='Nbgader course name')
    parser.add_argument('nbgrader_teacher_account', metavar='TEACHER', type=str,
                        help='Nbgrader teachers account name')
    parser.add_argument('--nbgrader_course_directory', '-d', metavar='COURSEDIR', type=str, nargs='?',
                        default=nbgrader_course_directory_template,
                        help='Path to nbgrader course directory root')
    parser.add_argument('--jupyterhub_config_filename', '-c', metavar='CONFIG', type=str, nargs='?',
                        default='/etc/jupyterhub/jupyterhub_config.py',
                        help='Path to jupyterhub config filename')
    parser.add_argument('--jupyterhub_service_port', '-p', metavar='PORT', type=int, nargs='?',
                        default=0,
                        help='Jupyterhub service port number')
    parser.add_argument('--jupyterhub_api_token', '-t', metavar='TOKEN', type=str, nargs='?',
                        default=jupyterhub_api_token,
                        help='Jupyterhub api_token')
    parser.add_argument('--nbgrader_course_header_include','-i', action='store_true',
                        help='Include nbgrader course header into course')
    parser.add_argument('--logging_level', '-l', metavar='LEVEL', type=str, nargs='?',
                        choices=list(logging_level.keys()),
                        default='INFO',
                        help='Logging level')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--nbgrader_students_filename', '-s', metavar='STUDENTSFILE', type=str, nargs='?',
                        default=None,    
                        help='Nbgrader add students from students csv filename to course')
    group.add_argument('--create_all','-a', action='store_true',
                        help='Run createAll')
 
    args = parser.parse_args()
    
    #
    # Convert logging level
    #

    args.logging_level = logging_level[args.logging_level]
    
    #
    # Create default CourseDirectory.root 
    #

    if args.nbgrader_course_directory == nbgrader_course_directory_template:
        args.nbgrader_course_directory = nbgrader_course_directory_template.replace('TEACHER',args.nbgrader_teacher_account).replace('COURSE',args.nbgrader_course_id)

    #
    # if nbgrader_students_filename is given, the course must already exist, so return here 
    #
    
    if args.nbgrader_students_filename:
        return args

    #
    # Create default port - looking for the last port in jupyterhub_config.py
    #

    if args.jupyterhub_service_port == 0:
        with open(args.jupyterhub_config_filename) as JHC:
            JHCcontent = JHC.read()
        # all ports for courses should start with the same first numbers (jupyterhub_service_port_startnumbers) and end up with three-digits ascending numbers
        searchpattern = f"'url': 'http://127.0.0.1:{jupyterhub_service_port_startnumbers}"
        indx = JHCcontent.rfind(searchpattern)
        if indx == -1:
            last_nr = 0
        else: 
            last_nr = int(JHCcontent[indx+len(searchpattern):indx+len(searchpattern)+3])
        args.jupyterhub_service_port = jupyterhub_service_port_startnumbers*1000+last_nr+1

    return args



if __name__ == '__main__':
    #
    # Systemwide variables - should be adopted to every installation
    #

    # jupyterhub_api_token
    jupyterhub_api_token = 'api_token'

    # if jupyterhub_service_port should be retrieved automatically,  
    # all jupyterhub_service_ports for courses should start with the same first numbers 
    # given in parameter jupyterhub_service_port_startnumbers and end up with three-digits ascending numbers
    jupyterhub_service_port_startnumbers = 19

    # template for home directories of teachers, TEACHER and COURSE will be replaced
    nbgrader_course_directory_template = '/home/TEACHER/Courses/COURSE'
    
    #
    # Parse arguments 
    #
    
    args = parseArguments(jupyterhub_api_token,
                          jupyterhub_service_port_startnumbers,
                          nbgrader_course_directory_template)
                          
    #
    # Additional systemwide variables, which are not useful to include it in arguments - should also be adopted to every installation
    #                      

    args.logging_separator = '-'*60
    args.logging_filename = f'{os.path.basename(__file__)}.log'
    args.logging_format = '[%(asctime)s: %(filename)s.%(lineno)s - %(levelname)s] %(message)s'
    args.jupyter_bin_command='/usr/bin/jupyter'

    #
    # Create a nbgrader course header 
    #
        
    if args.nbgrader_course_header_include:
        args.nbgrader_course_header_ipynb = nbformat.v4.new_notebook()
        #
        # Markdown cell text for first cell in jupyter notebook header.ipynb 
        #
        nb_markdown_cell = """# Consider the following hint

Enter your name into the following cell:
"""
        args.nbgrader_course_header_ipynb.cells.append(nbformat.v4.new_markdown_cell(nb_markdown_cell))
        #
        # Code cell source content for second cell in jupyter notebook header.ipynb 
        #
        nb_code_cell = "NAME = \"\""
        args.nbgrader_course_header_ipynb.cells.append(nbformat.v4.new_code_cell(nb_code_cell))
    else:
        args.nbgrader_course_header_ipynb = False

    #
    # Variables might also be overwritten here e.g. for testing
    #
    
    args.logging_level = logging.DEBUG
    #args.nbgrader_course_directory = f'{os.getcwd()}/TestNbgraderDir/{args.nbgrader_teacher_account}/Courses/{args.nbgrader_course_id}'

    #
    # Creating and starting logging
    #
    
    logging.basicConfig(filename=args.logging_filename,
                        format=args.logging_format,
                        level=args.logging_level)

    argsListing = '\n    '.join(f"{k}={args.__dict__[k]}" for k in args.__dict__)
    logging.info(f"Arguments parsed:\n{args.logging_separator}\n    {argsListing}\n{args.logging_separator}") 

    #
    # Creating an instance 
    #
    
    courseInstance = createMultipleCourse(**args.__dict__)

    #
    # Check for existing groups and services in jupyterhub config file (could be commented out, if already done)
    # 
    
    courseInstance.checkGroupsServicesInJHconfig()
    
    #
    # Running createAll
    #
    if args.create_all: courseInstance.createAll()
    
    #
    # Running addStudents2Course
    #
    if args.nbgrader_students_filename: courseInstance.addStudents2Course()


