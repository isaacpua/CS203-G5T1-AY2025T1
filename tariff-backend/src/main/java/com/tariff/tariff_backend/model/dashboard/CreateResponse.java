package com.tariff.tariff_backend.model.dashboard;

import lombok.Data;
import lombok.AllArgsConstructor;

@Data
@AllArgsConstructor
public class CreateResponse {
    
    private boolean success;
    private String message;
}
