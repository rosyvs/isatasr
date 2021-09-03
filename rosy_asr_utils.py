import re
import string
import docx
import Levenshtein
import pandas as pd
import numpy as np

def strip_punct(instr):
    newstr = ''
    for word in instr.split():
	# delete truncated words
        if word.endswith('-'): continue
 
        # delete commas inside numbers
        m = re.match(r'(\d*),(\d)', word)
        if m != None:
            word = word.replace(',', '')

        # strip punctuation- replace punctuation with space
        pstr = '.?!,:;()"'
        trantab = str.maketrans('','',pstr)
        word = word.translate(trantab)
        word = word.strip()

        newstr += ' ' + word
    newstr = newstr.strip()
    return newstr

def format_sentences(text):
    # function to format text or lists of text (e.g. asr, transcript) for wer computation. 
    # Converts from list to a single string and apply some text normalization operations
    # note that the norm_transcript function should be applied first to remove REV-specific keywords 

    if isinstance(text,list):
        text = ' '.join(text)
    text = text.replace('\n',' ') # replace newline with space
    text = re.sub('\s+',' ',text) # replace multiple space with single
    text = strip_punct(text)
    text = text.lower()
    text = [word.strip(string.punctuation) for word in text.split()]# remove punc except within words
    text = ' '.join(text) # convert from list to string of space-delimited words 
    return text

def norm_transcript(docx_fname, txt_fname):
    doc = docx.Document(docx_fname)
    doctext = [p.text for p in doc.paragraphs]

    # write unstripped transcript to .txt
    txt_fname_diarized = re.sub('.txt','_diarized.txt',txt_fname)
    with open(txt_fname_diarized,'w') as outfile:
        outfile.write('\n'.join(doctext))

    # strip the various Speaker IDs and crosstalk indicators  off
    doc_stripped = [re.sub('Speaker \d+:','',line) for line in doctext]
    doc_stripped = [re.sub('\w+:','',line) for line in doc_stripped]
    doc_stripped = [re.sub(r"\t",'',line) for line in doc_stripped]
    doc_stripped = [line  for line in doc_stripped if not re.match(r'^\s*$', line)] # remove blank lines
    doc_stripped = [re.sub("[\(\[].*?[\)\]]", " ", line) for line in doc_stripped] # remove sections in brackets or parens
    doc_stripped = [strip_punct(line)  for line in doc_stripped] # remove punct
    # write stripped transcript to txt
    with open(txt_fname,'w') as outfile:
        outfile.write('\n'.join(doc_stripped))


def align_words(ref,hyp):
    '''
    Aligns two lists of words and outputs the alignment and edit operations
        Parameters:
            ref: reference string
            hyp: hypothesis string


        Returns:
            aligned: a pandas dataframe representing the alignment, 1 row per word 
                with columns:
                    ref_ix: index of word in the reference 
                    hyp_ix: index of word in the hypothesis
                    reference: word from the reference
                    hypothesis: matched word in hypothesis
                    operation: symbolic representations of operation 
                        {'=' : match, 
                        '+':insertion,
                        '-' : deletion,
                        '<>' : substitution
                        }
                    index_edit_ops: index into the edit_ops variable pertaining to each row 
            edit_ops: data frame of word-level operations to go from ref -> hyp

    
    '''

    # get all words and encode as UTF-8 characters to get alignment operations at word-level
    lexicon = list(set(ref+hyp))
    word2digit = dict((lexicon[i],chr(i)) for i in range(0,len(lexicon)))
    asr_uni =  [word2digit[w] for w in hyp]
    trans_uni =  [word2digit[w] for w in ref]
    edit_ops = pd.DataFrame(Levenshtein.editops(''.join(trans_uni),''.join(asr_uni)),
        columns = ['operation','transcript_ix','asr_ix'])
    

    # align the sequences, starting with a dumb alignment where they start together, then inserting as necessary
    aligned_ref = ref.copy()
    aligned_hyp = hyp.copy()
    ix_edit_ops = [np.NaN] *len(aligned_ref)
    aligned_ops =['='] *len(aligned_ref)
    aligned_ref_ix = list(range(len(ref)))
    aligned_hyp_ix = list(range(len(hyp)))

    ins_count = 0 # counter for insertion operations which increase the length of the ref seq thus change the indices
    del_count = 0 # counter for deletion operations which increase the length of the hyp seq thus change the indices
    for [i,ops] in edit_ops.iterrows():
        if ops['operation'] == 'insert':
            aligned_ref.insert(ins_count+ops['transcript_ix'],'_')
            aligned_ops.insert(ins_count+ops['transcript_ix'],'+')
            aligned_ref_ix.insert(ins_count+ops['transcript_ix'],np.NaN)
            ix_edit_ops.insert(ins_count+ops['transcript_ix'],i)
            ins_count = ins_count+1

        if ops['operation'] == 'delete':
            aligned_hyp.insert(del_count+ops['asr_ix'],'_')
            aligned_ops[ins_count + ops['transcript_ix']] = '-'
            aligned_hyp_ix.insert(del_count+ops['asr_ix'],np.NaN)
            ix_edit_ops[ins_count + ops['transcript_ix']] = i
            del_count=del_count+1

        if ops['operation'] == 'replace':
            aligned_ops[ins_count+ ops['transcript_ix']] ='<>' 
            ix_edit_ops[ins_count+ ops['transcript_ix']] =i
           

    aligned = pd.DataFrame({
        'ref_ix':aligned_ref_ix,
        'hyp_ix':aligned_hyp_ix,
        'reference':aligned_ref,
        'hypothesis' : aligned_hyp ,
        'operation' : aligned_ops,
        'index_edit_ops' : ix_edit_ops})

    return aligned, edit_ops