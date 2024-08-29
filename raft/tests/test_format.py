import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from format import extract_final_answer, extract_context

def test_extract_final_answer():
    """
    Tests that the final answer is correctly extracted from the cot_answer
    """

    final_answer = extract_final_answer('To answer the question about when Robert J. Berdahl served in his position, we need to extract the relevant information from the context provided. The context states:\n\n##begin_quote##\n2004–2013 Robert J.\n##end_quote##\n\nFrom this, we can understand that Robert J. Berdahl served in his position from the year 2004 to the year 2013.\n\nNow, putting this information into a final answer:\n\n<ANSWER>: Robert J. Berdahl served in his position from 2004 to 2013.')
    assert final_answer == 'Robert J. Berdahl served in his position from 2004 to 2013.'

def test_extract_context():
    """
    Tests that the context is correctly extracted from the instruction
    """

    context = extract_context('<DOCUMENT>In 2015, Berkeley and its sister campus, UCSF, established the\nInnova tive Genomics Institute to develop CRISPR gene editing, and, in 2020, an anonym ous donor21st centurypledged $252 million to help fund a new center for computing and data science. For the 2020 fiscal year,\nBerkeley set a fundraising record, receiving over $1 billion in gifts and pledges, and two years later, it broke\nthat record, raising ove r $1.2 bi llion.[62][59][63][64]\nVarious research ethics, human rights, and animal rights advocates have been in conflict\nwith Berkeley.<\/DOCUMENT>\nWhat was the original name of the University of California, Berkeley before ')
    assert context == '<DOCUMENT>In 2015, Berkeley and its sister campus, UCSF, established the\nInnova tive Genomics Institute to develop CRISPR gene editing, and, in 2020, an anonym ous donor21st centurypledged $252 million to help fund a new center for computing and data science. For the 2020 fiscal year,\nBerkeley set a fundraising record, receiving over $1 billion in gifts and pledges, and two years later, it broke\nthat record, raising ove r $1.2 bi llion.[62][59][63][64]\nVarious research ethics, human rights, and animal rights advocates have been in conflict\nwith Berkeley.<\/DOCUMENT>'
