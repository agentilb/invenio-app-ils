# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2020 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test record delete."""

import pytest
from elasticsearch import VERSION as ES_VERSION

from invenio_app_ils.circulation.search import get_active_loan_by_item_pid
from invenio_app_ils.errors import ItemDocumentNotFoundError, \
    ItemHasActiveLoanError
from invenio_app_ils.pidstore.pids import ITEM_PID_TYPE
from invenio_app_ils.records.api import Item

lt_es7 = ES_VERSION[0] < 7


def test_update_item(db, testdata):
    """Test update item status."""

    def get_active_loan_pid_and_item_pid():
        for t in testdata["items"]:
            if t["status"] == "CAN_CIRCULATE":
                item_pid = dict(type=ITEM_PID_TYPE, value=t["pid"])
                active_loan = (
                    get_active_loan_by_item_pid(item_pid).execute().hits
                )
                total = (
                    active_loan.total if lt_es7 else active_loan.total.value
                )
                if total > 0:
                    return t["pid"], active_loan[0]["pid"]

    # change item status while is on loan
    item_pid, loan_pid = get_active_loan_pid_and_item_pid()
    item = Item.get_record_by_pid(item_pid)
    item["status"] = "MISSING"
    with pytest.raises(ItemHasActiveLoanError):
        item.commit()

    # change document to one that does not exist
    item = Item.get_record_by_pid("itemid-1")
    item["document_pid"] = "not_found_doc"
    with pytest.raises(ItemDocumentNotFoundError):
        item.commit()
