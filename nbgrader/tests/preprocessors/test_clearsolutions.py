import pytest

from textwrap import dedent
from nbgrader.preprocessors import ClearSolutions

from .base import BaseTestPreprocessor
from .. import create_code_cell, create_text_cell


@pytest.fixture
def preprocessor():
    return ClearSolutions()


class TestClearSolutions(BaseTestPreprocessor):

    def test_custom_solution_region(self):
        """Are the solution region delimeters properly formatted?"""
        pp = ClearSolutions(
            comment_mark="%",
            begin_solution_delimeter="!!foo",
            end_solution_delimeter="@@bar")
        assert pp.begin_solution == "%!!foo"
        assert pp.end_solution == "%@@bar"

    def test_replace_solution_region_code(self, preprocessor):
        """Are solution regions in code cells correctly replaced?"""
        cell = create_code_cell()
        replaced_solution = preprocessor._replace_solution_region(cell)
        assert replaced_solution
        assert cell.source == dedent(
            """
            print("something")
            # YOUR CODE HERE
            raise NotImplementedError()
            """
        ).strip()

    def test_replace_solution_region_text(self, preprocessor):
        """Are solution regions in text cells correctly replaced?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            this is the answer!
            ### END SOLUTION
            """
        ).strip()
        replaced_solution = preprocessor._replace_solution_region(cell)
        assert replaced_solution
        assert cell.source == "something something\nYOUR ANSWER HERE"

    def test_dont_replace_solution_region(self, preprocessor):
        """Is false returned when there is no solution region?"""
        cell = create_text_cell()
        replaced_solution = preprocessor._replace_solution_region(cell)
        assert not replaced_solution

    def test_replace_solution_region_no_end(self, preprocessor):
        """Is an error thrown when there is no end solution statement?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            this is the answer!
            """
        ).strip()

        with pytest.raises(RuntimeError):
            preprocessor._replace_solution_region(cell)

    def test_replace_solution_region_nested_solution(self, preprocessor):
        """Is an error thrown when there are nested solution statements?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            ### BEGIN SOLUTION
            this is the answer!
            ### END SOLUTION
            """
        ).strip()

        with pytest.raises(RuntimeError):
            preprocessor._replace_solution_region(cell)

    def test_preprocess_code_cell_student(self, preprocessor):
        """Is the student version of a code cell correctly preprocessed?"""
        cell = create_code_cell()

        cell = preprocessor.preprocess_cell(cell, {}, 1)[0]
        assert cell.source == dedent(
            """
            print("something")
            # YOUR CODE HERE
            raise NotImplementedError()
            """
        ).strip()

    def test_preprocess_code_solution_cell_solution_region(self, preprocessor):
        """Is a code solution cell correctly cleared when there is a solution region?"""
        cell = create_code_cell()
        cell.metadata['nbgrader'] = dict(solution=True)
        cell = preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert cell.source == dedent(
            """
            print("something")
            # YOUR CODE HERE
            raise NotImplementedError()
            """
        ).strip()
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_code_cell_solution_region(self, preprocessor):
        """Is a code cell correctly cleared when there is a solution region?"""
        cell = create_code_cell()
        cell = preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert cell.source == dedent(
            """
            print("something")
            # YOUR CODE HERE
            raise NotImplementedError()
            """
        ).strip()
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_code_solution_cell_no_region(self, preprocessor):
        """Is a code solution cell correctly cleared when there is no solution region?"""
        cell = create_code_cell()
        cell.source = """print("the answer!")"""
        cell.metadata['nbgrader'] = dict(solution=True)

        cell = preprocessor.preprocess_cell(cell, {}, 1)[0]
        assert cell.source == dedent(
            """
            # YOUR CODE HERE
            raise NotImplementedError()
            """
        ).strip()
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_code_cell_no_region(self, preprocessor):
        """Is a code cell not cleared when there is no solution region?"""
        cell = create_code_cell()
        cell.source = """print("the answer!")"""
        cell.metadata['nbgrader'] = dict()
        cell = preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert cell.source == """print("the answer!")"""
        assert not cell.metadata.nbgrader.get('solution', False)

    def test_preprocess_text_solution_cell_no_region(self, preprocessor):
        """Is a text grade cell correctly cleared when there is no solution region?"""
        cell = create_text_cell()
        cell.metadata['nbgrader'] = dict(solution=True)
        cell = preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert cell.source == "YOUR ANSWER HERE"
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_text_cell_no_region(self, preprocessor):
        """Is a text grade cell correctly cleared when there is no solution region?"""
        cell = create_text_cell()
        cell.metadata['nbgrader'] = dict()
        cell = preprocessor.preprocess_cell(cell, {}, 1)[0]

        assert cell.source == "this is the answer!\n"
        assert not cell.metadata.nbgrader.get('solution', False)

    def test_preprocess_text_solution_cell_region(self, preprocessor):
        """Is a text grade cell correctly cleared when there is a solution region?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            this is the answer!
            ### END SOLUTION
            """
        ).strip()
        cell.metadata['nbgrader'] = dict(solution=True)

        cell = preprocessor.preprocess_cell(cell, {}, 1)[0]
        assert cell.source == "something something\nYOUR ANSWER HERE"
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_text_cell_region(self, preprocessor):
        """Is a text grade cell correctly cleared when there is a solution region?"""
        cell = create_text_cell()
        cell.source = dedent(
            """
            something something
            ### BEGIN SOLUTION
            this is the answer!
            ### END SOLUTION
            """
        ).strip()

        cell = preprocessor.preprocess_cell(cell, {}, 1)[0]
        assert cell.source == "something something\nYOUR ANSWER HERE"
        assert cell.metadata.nbgrader['solution']

    def test_preprocess_notebook(self, preprocessor):
        """Is the test notebook processed without error?"""
        nb = self._read_nb("files/test.ipynb")
        preprocessor.preprocess(nb, {})

    def test_remove_celltoolbar(self, preprocessor):
        """Is the celltoolbar removed?"""
        nb = self._read_nb("files/test.ipynb")
        nb.metadata['celltoolbar'] = 'Create Assignment'
        nb = preprocessor.preprocess(nb, {})[0]
        assert 'celltoolbar' not in nb.metadata
