package com.tariff.tariff_backend.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class RateParser {
    public enum RateKind { //what kind of rate it is
        FREE,
        AD_VALOREM,                 // percent only
        SPECIFIC_PER_UNIT,          // specific only (per unit)
        COMBINED_ADVAL_PLUS_SPECIFIC, // both percent + specific
        COMPOSITE, //multiple of the things
        UNKNOWN
    }

    public record RateComponent(
        RateKind kind,
        BigDecimal adValorem,
        BigDecimal specificPerUnit, //bigdecimal is btr cos double and float will round off and idw that
        String unit, //"/kg", "/liter"
        String qualifier, //for stuff like "on the battery"/"drained weight" and what not
        String raw //original input (for debugging)
    ){}
    
    public record ParsedRate ( //record basically auto generate constructor and getters with equals and hashcode and tostrings
        String raw,
        List<RateComponent> components
    )
    {  public boolean isFree(){ //check if its 0 or if its the long words one (default to 0)
            for (RateComponent c : components){
                if (c.kind == RateKind.FREE || c.kind == RateKind.UNKNOWN){
                    continue;
                }

                if (c.kind == RateKind.AD_VALOREM && c.adValorem != null && c.adValorem.compareTo(BigDecimal.ZERO) == 0){
                    continue;
                } 

                if (c.kind == RateKind.SPECIFIC_PER_UNIT && c.specificPerUnit != null && c.specificPerUnit.compareTo(BigDecimal.ZERO) == 0 ){
                    continue;
                }
                //if anything else
                return false;
            }
            return true;
        }

        public RateKind overallKind(){ //to categorise things
            if (components.size() == 1){
                return components.get(0).kind();
            }

            boolean hasPercentage = false;
            boolean hasSpecifics = false;
            int count = 0;
            for (RateComponent c : components){
                if (c.kind == RateKind.AD_VALOREM && c.adValorem != null && c.adValorem.compareTo(BigDecimal.ZERO) > 0){
                    hasPercentage = true;
                    count++;
                }
                if (c.kind == RateKind.SPECIFIC_PER_UNIT && c.specificPerUnit != null && c.specificPerUnit.compareTo(BigDecimal.ZERO) > 0 ){
                    hasSpecifics = true;
                    count++;
                }
            }
            if (hasPercentage && hasSpecifics && count == 2) {
                return RateKind.COMBINED_ADVAL_PLUS_SPECIFIC;
            }
            return RateKind.COMPOSITE;
        }
    }



    private RateParser(){} //constructor

    //all the patterns, lowkey cos idk how to parse properly, so i have to js copy from gpt
    
    private static final Pattern FREE_ZERO = Pattern.compile("^\\s*0+(?:\\.0+)?%?\\s*$"); //matching 0.0,0.0%

    private static final Pattern PERCENT = Pattern.compile("^\\s*([+-]?\\d{1,3}(?:,\\d{3})*(?:\\.\\d+)?|[+-]?\\d+(?:\\.\\d+)?)\\s*%\\s*(.*)$", Pattern.CASE_INSENSITIVE);

    // "$1.556/kg", "0.12/kg", "$1.13/m3", "$1.34/1000"
    private static final Pattern DOLLAR_PER_UNIT = Pattern.compile("^\\s*\\$?\\s*([+-]?\\d+(?:\\.\\d+)?)\\s*/\\s*([a-zA-Z0-9^]+)\\s*(.*)$", Pattern.CASE_INSENSITIVE);

    // "13.7 cents/kg", "0.5 cents/kg", "2.8 cents/doz.", "89.6 cents/1000"
    private static final Pattern CENTS_PER_UNIT = Pattern.compile("^\\s*([+-]?\\d+(?:\\.\\d+)?)\\s*(?:c|cent|cents|¢)\\s*(?:/(.+?)|\\s+(each|jewel|bbl))?\\s*(.*)$", Pattern.CASE_INSENSITIVE);

    // number without the % or wtv incase got any tariff value written as only numbers
    private static final Pattern NUMBER_ONLY = Pattern.compile("^\\s*([+-]?\\d+(?:\\.\\d+)?)\\s*(.*)$");

    // for the cents/kg + % and stuff like that
    private static final Pattern PLUS_SPLIT = Pattern.compile("\\s*\\+\\s*");

    //main parsing method
    public static ParsedRate parse(String input){

        if (input == null) {
            return new ParsedRate(input, List.of()); //empty list
        }
        input = input.trim();
        if (FREE_ZERO.matcher(input).matches()){
            RateComponent r = new RateComponent(RateKind.FREE, BigDecimal.ZERO, BigDecimal.ZERO, null, null, input);
            return new ParsedRate(input, List.of(r));
        }

        String[] parts = PLUS_SPLIT.split(input,-1);
        List<RateComponent> components = new ArrayList<>(parts.length);
        for (String part : parts){
            components.add(singularParse(part));
        }
        return new ParsedRate(input, components);
    }

    //my helpers
    private static RateComponent singularParse(String splitString){ //extracting the percent/cents/dollars or wtv
        String str = splitString.trim();

        //Im gonna try to match everything with the matcher class and pattern class
        
        Matcher mp = PERCENT.matcher(str); //for the percent
        if (mp.matches()){ 
            BigDecimal pct = new BigDecimal(mp.group(1)); //group(1) is the part inside parentheses "%17" --> "17"
            pct = pct.movePointLeft(2);
            String qualifier = extractQualifier(mp.group(2));
            return new RateComponent(RateKind.AD_VALOREM, pct, BigDecimal.ZERO, null, qualifier, str);

        }

        Matcher mc = CENTS_PER_UNIT.matcher(str);
        if (mc.matches()){
            BigDecimal cents = new BigDecimal(mc.group(1));
            String slashUnits = mc.group(2);
            String wordUnits = mc.group(3);
            String tail = (mc.group(4));

            String unit = normaliseUnit(firstNonBlank(slashUnits,wordUnits, "each"));
            String qualifier = extractQualifier(tail);
            return new RateComponent(RateKind.SPECIFIC_PER_UNIT, BigDecimal.ZERO, cents.movePointLeft(2), unit, qualifier, str);

        }

        Matcher md = DOLLAR_PER_UNIT.matcher(str);
        if (md.matches()) {
            BigDecimal dollars = new BigDecimal(md.group(1));
            String unitToken = md.group(2);
            String tail = md.group(3);

            String unit = normaliseUnit(unitToken);
            String qualifier = extractQualifier(tail);

            return new RateComponent(RateKind.SPECIFIC_PER_UNIT, BigDecimal.ZERO, dollars, unit, qualifier, str);

        }

        Matcher mn = NUMBER_ONLY.matcher(str);
        if (mn.matches()) {
            BigDecimal num  = new BigDecimal(mn.group(1));
            String tail = mn.group(2);
            String qualifier = extractQualifier(tail);
            BigDecimal frac = num.compareTo(BigDecimal.ONE) > 0 ? num.movePointLeft(2) : num;
            return new RateComponent(RateKind.AD_VALOREM, frac, BigDecimal.ZERO, null, qualifier, str);
        }
        return new RateComponent(RateKind.UNKNOWN, BigDecimal.ZERO, BigDecimal.ZERO, null, null, str);
    } 

    private static String extractQualifier(String tail){
        if (tail == null || tail.isBlank()) {
            return null;
        }
        tail = tail.trim();
        if (tail.toLowerCase().startsWith("on ")){
            return tail;
        }
        return null;
    }

    private static String firstNonBlank(String... vals){//doing String... vals lets u pass in multiple strings and it will see it as an array
        for (String v : vals){
            if (v != null && !v.isBlank()){
                return v;
            }
        }
        return null; //if all are blank
    }

    private static String normaliseUnit(String rawUnitToken) { //i tried to find all the cases i could and just stuff i thought it might be
        if (rawUnitToken == null) return null;
        
        String unit = rawUnitToken.trim().toLowerCase();
        unit = unit.replaceAll("\\.$", "");
        unit = unit.replaceAll("\\s+", " ").trim();

        switch (unit) {
            case "kg", "kilogram", "kilograms" -> { return "/kg"; }
            case "l", "liter", "litre", "liters", "litres" -> { return "/liter"; }
            case "doz", "dozen" -> { return "/doz"; }
            case "unit", "piece", "each" -> { return "/unit"; }
            case "gross" -> { return "/gross"; }
            case "m3", "m^3", "cubicmeter", "cubicmeters" -> { return "/m3"; }
            case "m2", "m^2", "squaremeter", "squaremeters" -> { return "/m2"; }
            case "m", "meter", "meters" -> { return "/m"; }
            case "pc", "pcs", "pieces" -> { return "/unit"; }
            case "jewel", "jewels" -> { return "/jewel"; }
            case "bbl", "barrel", "barrels" -> { return "/bbl"; }
        }

        unit = unit.replaceAll("^per\\s+", "");
        unit = unit.replace(",", "");

        if (unit.matches("\\d+\\s+\\w[\\w\\-]*")) {
            return "/" + unit;
        }

        return "/" + unit;
    }
}
