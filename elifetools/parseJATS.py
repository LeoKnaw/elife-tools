from bs4 import BeautifulSoup
import cgi
import htmlentitydefs
import os
import time
import calendar
from slugify import slugify
from utils import *
import rawJATS as raw_parser


import logging
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler(os.getcwd() + os.sep + 'test.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)


def parse_xml(xml):
    return BeautifulSoup(xml, ["lxml", "xml"])

def parse_document(filelocation):
    return parse_xml(open(filelocation))


def title(soup):
    return node_text(raw_parser.title(soup))

def title_short(soup):
    "'title' truncated to 20 chars"
    # TODO: 20 is arbitrary, 
    return title(soup)[:20]

def title_slug(soup):
    "'title' slugified"
    return slugify(title(soup))

def doi(soup):
    # the first non-nil value returned by the raw parser
    return node_text(raw_parser.doi(soup))

def journal_id(soup):
    return node_text(raw_parser.journal_id(soup))

def journal_title(soup):
    return node_text(raw_parser.journal_title(soup))

def journal_issn(soup, pub_format = None):
    if pub_format:
        return node_text(raw_parser.journal_issn(soup, pub_format))

def publisher(soup):
    return node_text(raw_parser.publisher(soup))

def article_type(soup):
    # no node text extraction required
    return raw_parser.article_type(soup)

def article_meta_aff(soup):
    return node_text(raw_parser.article_meta_add(soup))
    
def keyword_group(soup):
    return raw_parser.keyword_group(soup) # doesn't actually do anything?

# DEPRECATED: use `keyword_group` avoid 'getters' and unnecessary abbreviations
def get_kwd_group(soup):
    return keyword_group(soup)

@strippen
def acknowledgements(soup):
    return node_text(raw_parser.acknowledgements(soup))

# DEPRECATED: use `acknowledgements`. avoid unnecessary abbreviations
def ack(soup):
    return acknowledgements(soup)

@nullify
@strippen
def conflict(soup):
    return map(node_text, raw_parser.conflict(soup))

def copyright_statement(soup):
    return node_text(raw_parser.copyright_statement(soup))

@inten
def copyright_year(soup):
    return node_text(raw_parser.copyright_year(soup))

def copyright_holder(soup):
    return node_text(raw_parser.copyright_holder(soup))

def license(soup):
    return node_text(raw_parser.licence_p(soup))

def license_url(soup):
    return raw_parser.licence_url(soup)

def funding_statement(soup):
    return node_text(raw_parser.funding_statement(soup))


#
# authors
#

#
# refs
#


def ref_text(ref):
    # ref - human readable full reference text
    ref_text = tag.get_text()
    ref_text = strip_strings(ref_text)
    # Remove excess space
    ref_text = ' '.join(ref_text.split())
    # Fix punctuation spaces and extra space
    ref_text = strip_punctuation_space(strip_strings(ref_text))
    return ref_text








#
# HERE BE MONSTERS
#


def authors(soup):
    """Find and return all the authors"""
    tags = extract_nodes(soup, "contrib", attr = "contrib-type", value = "author")
    authors = []
    position = 1
    
    article_doi = doi(soup)
    
    for tag in tags:
        author = {}
        
        # Person id
        try:
            person_id = tag["id"]
            person_id = person_id.replace("author-", "")
            author['person_id'] = int(person_id)
        except(KeyError):
            pass

        # Equal contrib
        try:
            equal_contrib = tag["equal-contrib"]
            if(equal_contrib == 'yes'):
                author['equal_contrib'] = True
        except(KeyError):
            pass
        
        # Correspondence
        try:
            corresponding = tag["corresp"]
            if(corresponding == 'yes'):
                author['corresponding'] = True
        except(KeyError):
            pass
        
        # Surname
        surname = extract_node_text(tag, "surname")
        if(surname != None):
            author['surname'] = surname

        # Given names
        given_names = extract_node_text(tag, "given-names")
        if(given_names != None):
            author['given_names'] = given_names
        
        # Find and parse affiliations
        affs = extract_nodes(tag, "xref", attr = "ref-type", value = "aff")
        if(len(affs) > 0):
            # One or more affiliations
            if(len(affs) > 1):
                # Prepare for multiple affiliations if multiples found
                author['country'] = []
                author['institution'] = []
                author['department'] = []
                author['city'] = []
                
            for aff in affs:
                # Find the matching affiliation detail
                rid = aff['rid']

                aff_node = extract_nodes(soup, "aff", attr = "id", value = rid)
                country = extract_node_text(aff_node[0], "country")
                
                # Institution is the tag with no attribute
                institutions = extract_nodes(aff_node[0], "institution")
                institution = None
                for inst in institutions:
                    try:
                        if(inst["content-type"] != None):
                            # A tag attribute found, skip it
                            pass
                    except KeyError:
                        institution = inst.text
                       
                # Department tag does have an attribute
                department = extract_node_text(aff_node[0], "institution", attr = "content-type", value = "dept")
                city = extract_node_text(aff_node[0], "named-content", attr = "content-type", value = "city")
                
                # Convert None to empty string if there is more than one affiliation
                if((country == None) and (len(affs) > 1)):
                    country = ''
                if((institution == None) and (len(affs) > 1)):
                    institution = ''
                if((department == None) and (len(affs) > 1)):
                    department = ''
                if((city == None) and (len(affs) > 1)):
                    city = ''
                    
                # Append values
                try:
                    # Multiple values
                    author['country'].append(country)
                except(KeyError):
                    author['country'] = country
                try:
                    # Multiple values
                    author['institution'].append(institution)
                except(KeyError):
                    author['institution'] = institution
                try:
                    # Multiple values
                    author['department'].append(department)
                except(KeyError):
                    author['department'] = department
                try:
                    # Multiple values
                    author['city'].append(city)
                except(KeyError):
                    author['city'] = city

        # Author - given names + surname
        author_name = ""
        if(given_names != None):
            author_name += given_names + " "
        if(surname != None):
            author_name += surname
        author['author'] = author_name
        
        # Add xref linked correspondence author notes if applicable
        cors = extract_nodes(tag, "xref", attr = "ref-type", value = "corresp")
        if(len(cors) > 0):
            # One or more 
            if(len(cors) > 1):
                # Prepare for multiple values if multiples found
                author['notes_correspondence'] = []
                
            for cor in cors:
                # Find the matching affiliation detail
                rid = cor['rid']

                # Find elements by id
                try:
                    corresp_node = soup.select("#" + rid)
                    author_notes = corresp_node[0].get_text()
                    author_notes = strip_strings(author_notes)
                except:
                    continue
                try:
                    # Multiple values
                    author['notes_correspondence'].append(author_notes)
                except(KeyError):
                    author['notes_correspondence'] = author_notes
                    
        # Add xref linked footnotes if applicable
        fns = extract_nodes(tag, "xref", attr = "ref-type", value = "fn")
        if(len(fns) > 0):
            # One or more 
            if(len(fns) > 1):
                # Prepare for multiple values if multiples found
                author['notes_footnotes'] = []
                
            for fn in fns:
                # Find the matching affiliation detail
                rid = fn['rid']

                # Find elements by id
                try:
                    fn_node = soup.select("#" + rid)
                    fn_text = fn_node[0].get_text()
                    fn_text = strip_strings(fn_text)
                except:
                    continue
                try:
                    # Multiple values
                    author['notes_footnotes'].append(fn_text)
                except(KeyError):
                    author['notes_footnotes'] = fn_text
                    
        # Add xref linked other notes if applicable, such as funding detail
        others = extract_nodes(tag, "xref", attr = "ref-type", value = "other")
        if(len(others) > 0):
            # One or more 
            if(len(others) > 1):
                # Prepare for multiple values if multiples found
                author['notes_other'] = []
                
            for other in others:
                # Find the matching affiliation detail
                rid = other['rid']

                # Find elements by id
                try:
                    other_node = soup.select("#" + rid)
                    other_text = other_node[0].get_text()
                    other_text = strip_strings(other_text)
                except:
                    continue
                try:
                    # Multiple values
                    author['notes_other'].append(other_text)
                except(KeyError):
                    author['notes_other'] = other_text    

        # If not empty, add position value, append, then increment the position counter
        if(len(author) > 0):
            author['article_doi'] = article_doi
            
            author['position'] = position
                        
            authors.append(author)
            position += 1
        
    return authors

def references(soup):
    """Renamed to refs"""
    return refs(soup)
    
def refs(soup):
    """Find and return all the references"""
    tags = extract_nodes(soup, "ref")
    refs = []
    position = 1
    
    article_doi = doi(soup)
    
    for tag in tags:
        ref = {}
        
        # etal
        etal = extract_nodes(tag, "etal")
        try:
            if(etal[0]):
                ref['etal'] = True
        except(IndexError):
            pass
        
        # ref - human readable full reference text
        ref_text = tag.get_text()
        ref_text = strip_strings(ref_text)
        # Remove excess space
        ref_text = ' '.join(ref_text.split())
        # Fix punctuation spaces and extra space
        ref['ref'] = strip_punctuation_space(strip_strings(ref_text))
        
        # article_title
        article_title = extract_node_text(tag, "article-title")
        if(article_title != None):
            ref['article_title'] = article_title
            
        # year
        year = extract_node_text(tag, "year")
        if(year != None):
            ref['year'] = year
            
        # source
        source = extract_node_text(tag, "source")
        if(source != None):
            ref['source'] = source
            
        # publication_type
        mixed_citation = extract_nodes(tag, "mixed-citation")
        try:
            publication_type = mixed_citation[0]["publication-type"]
            ref['publication_type'] = publication_type
        except(KeyError, IndexError):
            pass

        # authors
        person_group = extract_nodes(tag, "person-group")
        authors = []
        try:
            name = extract_nodes(person_group[0], "name")
            for n in name:
                surname = extract_node_text(n, "surname")
                given_names = extract_node_text(n, "given-names")
                # Convert all to strings in case a name component is missing
                if(surname is None):
                    surname = ""
                if(given_names is None):
                    given_names = ""
                full_name = strip_strings(surname + ' ' + given_names)
                authors.append(full_name)
            if(len(authors) > 0):
                ref['authors'] = authors
        except(KeyError, IndexError):
            pass
            
        # volume
        volume = extract_node_text(tag, "volume")
        if(volume != None):
            ref['volume'] = volume
            
        # fpage
        fpage = extract_node_text(tag, "fpage")
        if(fpage != None):
            ref['fpage'] = fpage
            
        # lpage
        lpage = extract_node_text(tag, "lpage")
        if(lpage != None):
            ref['lpage'] = lpage
            
        # collab
        collab = extract_node_text(tag, "collab")
        if(collab != None):
            ref['collab'] = collab
            
        # publisher_loc
        publisher_loc = extract_node_text(tag, "publisher-loc")
        if(publisher_loc != None):
            ref['publisher_loc'] = publisher_loc
        
        # publisher_name
        publisher_name = extract_node_text(tag, "publisher-name")
        if(publisher_name != None):
            ref['publisher_name'] = publisher_name
            
        # If not empty, add position value, append, then increment the position counter
        if(len(ref) > 0):
            ref['article_doi'] = article_doi
            
            ref['position'] = position
                        
            refs.append(ref)
            position += 1
    
    return refs

def components(soup):
    """
    Find the components, i.e. those parts that would be assigned
    a unique component DOI, such as figures, tables, etc.
    """
    components = []
    
    component_types = ["abstract", "fig", "table-wrap", "media",
                       "chem-struct-wrap", "sub-article", "supplementary-material",
                       "boxed-text"]
    
    position = 1
    
    article_doi = doi(soup)
    
    # Find all tags for all component_types, allows the order
    #  in which they are found to be preserved
    tags = soup.find_all(component_types) 
    
    for tag in tags:
        
        component = {}
        
        # Component type is the tag's name
        ctype = tag.name
        
        # First find the doi if present
        if(ctype == "sub-article"):
            object_id = extract_node_text(tag, "article-id", attr = "pub-id-type", value = "doi")
        else:
            object_id = extract_node_text(tag, "object-id", attr = "pub-id-type", value = "doi")
        if(object_id is not None):
            component['doi'] = object_id
            component['doi_url'] = 'http://dx.doi.org/' + object_id
        else:
            # If no object-id is found, then skip this component
            continue

        content = ""
        for p_tag in extract_nodes(tag, "p"):
            if content != "":
                # Add a space before each new paragraph for now
                content = content + " "
            content = content + node_text(p_tag)
            
        if(content != ""):
            component['content'] = content
    
        if(len(component) > 0):
            component['article_doi'] = article_doi
            component['type'] = ctype
            component['position'] = position
                        
            components.append(component)
            position += 1
    
    return components

@strippen
def abstract(soup):
    """
    Find the article abstract and format it
    """

    abstract_soup = []
    # Strip out the object-id so we only have the text
    try:
        abstract_soup = soup.find_all("abstract")
    except(IndexError):
        # No abstract found
        pass

    # Find the desired abstract node, <abstract>
    abstract_node = None
    for tag in abstract_soup:
        try:
            if(tag["abstract-type"] != None):
                # A tag attribute found, skip it
                pass
        except KeyError:
                # No attribute, use this abstract
                abstract_node = tag
                break
    
    # Shortcut: if no abstract found, return none
    if(abstract_node == None):
        return None

    # Allow the contents of certain markup tags, then
    #  remove any tags and their contents not on the allowed list
    allowed_tags = ["italic", "sup", "p"]

    for allowed in allowed_tags:
        tag = abstract_node.find_all(allowed)
        for t in tag:
            t.unwrap()
    
    # Done unwrapping allowed tags, now delete tags and enclosed
    # content of unallowed tags
    all = abstract_node.find_all()

    extracted_tags = []
    for a in all:
        # Extract the tags we do not want text from, and we will insert the tags back later
        #  using clear() will destroy them for good, and breaks the getting components by DOI
        extracted_tags.append(a.extract())
        #a.clear()

    abstract = abstract_node.text

    # Put the extracted tags back in, hacky as the original order is not preserved
    for et in extracted_tags:
        abstract_node.insert(0, et)
    
    return abstract


@strippen
def subject_area(soup):
    """
    Find the subject areas from article-categories subject tags
    """
    subject_area = []
    try:
        article_meta = extract_nodes(soup, "article-meta")
        article_categories = extract_nodes(article_meta[0], "article-categories")
        subj_group = extract_nodes(article_categories[0], "subj-group")
        for tag in subj_group:
            tags = extract_nodes(tag, "subject")
            for t in tags:
                subject_area.append(t.text)
                
    except(IndexError):
        # Tag not found
        return None
    
    return subject_area

@nullify
def research_organism(soup):
    """
    Find the research-organism from the set of kwd-group tags
    """
    research_organism = []
    kwd_group = get_kwd_group(soup)
    for tag in kwd_group:
        try:
            if(tag["kwd-group-type"] == "research-organism" or tag["kwd-group-type"] == "Research-organism"):
                tags = extract_nodes(tag, "kwd")
                for t in tags:
                    research_organism.append(t.text)
        except KeyError:
            continue
    return research_organism

@nullify
def keywords(soup):
    """
    Find the keywords from the set of kwd-group tags
    """
    keywords = []
    kwd_group = get_kwd_group(soup)
    for tag in kwd_group:
        try:
            if(tag["kwd-group-type"] != None):
                # A tag attribute found, check it for correct attribute
                if(tag["kwd-group-type"] == "author-keywords"):
                    keyword_text_list = get_kwd(tag)
                    for k in keyword_text_list:
                        keywords.append(k)
        except KeyError:
            # Tag attribute not found, we want this tag value
            keyword_text_list = get_kwd(tag)
            for k in keyword_text_list:
                keywords.append(k)

    return keywords

@nullify
def get_kwd(tag):
    """
    For extracting individual keywords (kwd) from a parent kwd-group
    refactored to use more than once in def keywords
    """
    keywords = []
    kwd = extract_nodes(tag, "kwd")
    for k in kwd:
        keywords.append(k.text)
    return keywords

@nullify
@strippen
def correspondence(soup):
    """
    Find the corresp tags included in author-notes
    for primary correspondence
    """
    correspondence = []
    try:
        author_notes = extract_nodes(soup, "author-notes")
        tags = extract_nodes(author_notes[0], "corresp")
        for tag in tags:
            correspondence.append(tag.text)
    except(IndexError):
        # Tag not found
        return None
    return correspondence

@nullify
@strippen
def author_notes(soup):
    """
    Find the fn tags included in author-notes
    """
    author_notes = []
    try:
        author_notes_section = extract_nodes(soup, "author-notes")
        fn = extract_nodes(author_notes_section[0], "fn")
        for f in fn:
            try:
                if(f['fn-type'] != 'present-address'):
                    author_notes.append(f.text)
                else:
                    # Throw it away if it is a present-address footnote
                    continue
            except(KeyError):
                # Append if the fn-type attribute does not exist
                author_notes.append(f.text)
    except(IndexError):
        # Tag not found
        return None
    return author_notes

def get_ymd(soup):
    """
    Get the year, month and day from child tags
    """
    day = extract_node_text(soup, "day")
    month = extract_node_text(soup, "month")
    year = extract_node_text(soup, "year")
    return (day, month, year)

def get_pub_date(soup, date_type = "pub"):
    """
    Find the publishing date for populating
    pub_date_date, pub_date_day, pub_date_month, pub_date_year, pub_date_timestamp
    Default date_type is pub
    """
    tz = "UTC"
    
    try:
        pub_date_section = extract_nodes(soup, "pub-date", attr = "date-type", value = date_type)
        if(len(pub_date_section) == 0):
            pub_date_section = extract_nodes(soup, "pub-date", attr = "date-type", value = date_type)
        (day, month, year) = get_ymd(pub_date_section[0])

    except(IndexError):
        # Tag not found, try the other
        return None
    
    date_struct = None
    try:
        date_struct = time.strptime(year + "-" + month + "-" + day + " " + tz, "%Y-%m-%d %Z")
    except(TypeError):
        # Date did not convert
        pass

    return date_struct

def pub_date_date(soup):
    """
    Find the publishing date pub_date_date in human readable form
    """
    pub_date = get_pub_date(soup)
    date_string = None
    try:
        date_string = time.strftime("%B %d, %Y", pub_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string

@inten
def pub_date_day(soup):
    """
    Find the publishing date pub_date_day
    """
    pub_date = get_pub_date(soup)
    date_string = None
    try:
        date_string =  time.strftime("%d", pub_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string

@inten
def pub_date_month(soup):
    """
    Find the publishing date pub_date_day
    """
    pub_date = get_pub_date(soup)
    date_string = None
    try:
        date_string = time.strftime("%m", pub_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string
    
@inten
def pub_date_year(soup):
    """
    Find the publishing date pub_date_day
    """
    pub_date = get_pub_date(soup)
    date_string = None
    try:
        date_string = time.strftime("%Y", pub_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string

def pub_date_timestamp(soup):
    """
    Find the publishing date pub_date_timestamp, in UTC time
    """
    pub_date = get_pub_date(soup)
    timestamp = None
    try:
        timestamp = calendar.timegm(pub_date)
    except(TypeError):
        # Date did not convert
        pass
    return timestamp

def get_history_date(soup, date_type = None):
    """
    Find a date in the history tag for the specific date_type
    typical date_type values: received, accepted
    """
    if(date_type == None):
        return None
    
    tz = "UTC"
    
    try:
        history_section = extract_nodes(soup, "history")
        history_date_section = extract_nodes(soup, "date", attr = "date-type", value = date_type)
        (day, month, year) = get_ymd(history_date_section[0])
    except(IndexError):
        # Tag not found, try the other
        return None
    return time.strptime(year + "-" + month + "-" + day + " " + tz, "%Y-%m-%d %Z")

def received_date_date(soup):
    """
    Find the received date received_date_date in human readable form
    """
    received_date = get_history_date(soup, date_type = "received")
    date_string = None
    try:
        date_string = time.strftime("%B %d, %Y", received_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string

@inten
def received_date_day(soup):
    """
    Find the received date received_date_day
    """
    received_date = get_history_date(soup, date_type = "received")
    date_string = None
    try:
        date_string = time.strftime("%d", received_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string

@inten
def received_date_month(soup):
    """
    Find the received date received_date_day
    """
    received_date = get_history_date(soup, date_type = "received")
    date_string = None
    try:
        date_string = time.strftime("%m", received_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string
    
@inten
def received_date_year(soup):
    """
    Find the received date received_date_day
    """
    received_date = get_history_date(soup, date_type = "received")
    date_string = None
    try:
        date_string = time.strftime("%Y", received_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string

def received_date_timestamp(soup):
    """
    Find the received date received_date_timestamp, in UTC time
    """
    received_date = get_history_date(soup, date_type = "received")
    timestamp = None
    try:
        timestamp = calendar.timegm(received_date)
    except(TypeError):
        # Date did not convert
        pass
    return timestamp
    
def accepted_date_date(soup):
    """
    Find the accepted date accepted_date_date in human readable form
    """
    accepted_date = get_history_date(soup, date_type = "accepted")
    date_string = None
    try:
        date_string = time.strftime("%B %d, %Y", accepted_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string

@inten
def accepted_date_day(soup):
    """
    Find the accepted date accepted_date_day
    """
    accepted_date = get_history_date(soup, date_type = "accepted")
    date_string = None
    try:
        date_string = time.strftime("%d", accepted_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string

@inten
def accepted_date_month(soup):
    """
    Find the accepted date accepted_date_day
    """
    accepted_date = get_history_date(soup, date_type = "accepted")
    date_string = None
    try:
        date_string = time.strftime("%m", accepted_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string
    
@inten
def accepted_date_year(soup):
    """
    Find the accepted date accepted_date_day
    """
    accepted_date = get_history_date(soup, date_type = "accepted")
    date_string = None
    try:
        date_string = time.strftime("%Y", accepted_date)
    except(TypeError):
        # Date did not convert
        pass
    return date_string

def accepted_date_timestamp(soup):
    """
    Find the accepted date accepted_date_timestamp, in UTC time
    """
    accepted_date = get_history_date(soup, date_type = "accepted")
    timestamp = None
    try:
        timestamp = calendar.timegm(accepted_date)
    except(TypeError):
        # Date did not convert
        pass
    return timestamp

def get_funding_group(soup):
    """
    Get the funding-group sections for populating
    funding_source lists
    """
    funding_group_section = extract_nodes(soup, "funding-group")
    return funding_group_section

@nullify
def award_groups(soup):
    """
    Find the award-group items and return a list of details
    """
    award_groups = []
    
    funding_group_section = get_funding_group(soup)
    for fg in funding_group_section:
        
        award_group_tags = extract_nodes(fg, "award-group")
        
        for ag in award_group_tags:
        
            award_group = {}
            
            award_group['funding_source'] = award_group_funding_source(ag)
            award_group['recipient'] = award_group_principal_award_recipient(ag)
            award_group['award_id'] = award_group_award_id(ag)
            
            award_groups.append(award_group)
    
    return award_groups


@nullify
def award_group_funding_source(tag):
    """
    Given a funding group element
    Find the award group funding sources, one for each
    item found in the get_funding_group section
    """
    award_group_funding_source = []
    funding_source_tags = extract_nodes(tag, "funding-source")
    for t in funding_source_tags:
        award_group_funding_source.append(t.text)
    return award_group_funding_source

@nullify
def award_group_award_id(tag):
    """
    Find the award group award id, one for each
    item found in the get_funding_group section
    """
    award_group_award_id = []
    award_id_tags = extract_nodes(tag, "award-id")
    for t in award_id_tags:
        award_group_award_id.append(t.text)
    return award_group_award_id

@nullify
def award_group_principal_award_recipient(tag):
    """
    Find the award group principal award recipient, one for each
    item found in the get_funding_group section
    """
    award_group_principal_award_recipient = []
    principal_award_recipients = extract_nodes(tag, "principal-award-recipient")
    
    for t in principal_award_recipients:
        principal_award_recipient_text = ""
        
        try:
            institution = extract_node_text(t, "institution")
            surname = extract_node_text(t, "surname")
            given_names = extract_node_text(t, "given-names")
            # Concatenate name and institution values if found
            #  while filtering out excess whitespace
            if(given_names):
                principal_award_recipient_text += given_names
            if(principal_award_recipient_text != ""):
                principal_award_recipient_text += " "
            if(surname):
                principal_award_recipient_text += surname
            if(institution and len(institution) > 1):
                if(principal_award_recipient_text != ""):
                    principal_award_recipient_text += ", "
                principal_award_recipient_text += institution
        except IndexError:
            continue
        award_group_principal_award_recipient.append(principal_award_recipient_text)
    return award_group_principal_award_recipient
