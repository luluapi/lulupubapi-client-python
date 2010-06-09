import publish.client.client as client
import publish.common.project as project
import os.path

def create_hardcover(self):
    """
    Create a hardcover book.
    """
    cover = "./path/to/file/6x9_60p_jacket_cover.pdf"
    contents = "./path/to/file/6x9_60p.pdf"
    assert os.path.exists(cover), "interior file for test does not exist"
    assert os.path.exists(contents), "interior file for test does not exist"
    pclient = client.Client()

    # This login depends on having user and key set in ~/.lulu_publish_api.conf.
    # Alternatively, credentials can be passed into the login() function.
    pclient.login()

    result = pclient.request_upload_token()
    data = pclient.upload([cover, contents], result['token'])

    cover_fd = project.FileDetails({"mimetype": "application/pdf", "filename": os.path.basename(cover) })
    contents_fd = project.FileDetails({"mimetype": "application/pdf", "filename": os.path.basename(contents) })

    proj = project.Project()
    proj.set("project_type", "hardcover")
    proj.set("allow_ratings", False)
    proj.set("bibliography", project.Bibliography())
    proj.get("bibliography").set("title",  "Books...With Jackets")
    proj.get("bibliography").set("authors", [ {"first_name": "arthur", "last_name":  "the author"}, ])
    proj.get("bibliography").set("category",  1)
    proj.get("bibliography").set("description",  "read it, you'll like it")
    proj.get("bibliography").set("keywords",  [ "cat and dog", "pickle" ])
    proj.get("bibliography").set("license",  "Public Domain")
    proj.get("bibliography").set("copyright_year",  2000)
    proj.get("bibliography").set("copyright_citation",  "by Arthur Author")
    proj.get("bibliography").set("publisher",  "Lulu.com")
    proj.get("bibliography").set("edition",  "First")
    proj.get("bibliography").set("language",  "EN")
    proj.get("bibliography").set("country_code",  "US")
    proj.set("physical_attributes", project.PhysicalAttributes())
    proj.get("physical_attributes").set("binding_type", "jacket-hardcover")
    proj.get("physical_attributes").set("trim_size", "US_TRADE")
    proj.get("physical_attributes").set("paper_type", "regular")
    proj.get("physical_attributes").set("color", False)
    proj.set("access", "private")
    proj.set("pricing", [ 
            project.Pricing({"product": "download", "currency_code": "EUR", "total_price": "15.00"}),
            project.Pricing({"product": "print", "currency_code": "EUR", "total_price": "39.95"}),
        ])
    proj.set("file_info", project.FileInfo({ "contents": [ contents_fd ], "cover": [ cover_fd ] }))

    data = pclient.create(proj)
    assert data.has_key('content_id')
    assert data['content_id'] > 0
