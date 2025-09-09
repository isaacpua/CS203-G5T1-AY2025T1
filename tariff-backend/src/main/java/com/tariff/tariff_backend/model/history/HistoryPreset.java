package com.tariff.tariff_backend.model.history;

public class HistoryPreset {
    private String title;
    private String reporter;
    private String partner;
    private String itemCode;

    public HistoryPreset() {}
    public HistoryPreset(String title, String reporter, String partner, String itemCode) {
        this.title = title; this.reporter = reporter; this.partner = partner; this.itemCode = itemCode;
    }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getReporter() { return reporter; }
    public void setReporter(String reporter) { this.reporter = reporter; }
    public String getPartner() { return partner; }
    public void setPartner(String partner) { this.partner = partner; }
    public String getItemCode() { return itemCode; }
    public void setItemCode(String itemCode) { this.itemCode = itemCode; }
}
