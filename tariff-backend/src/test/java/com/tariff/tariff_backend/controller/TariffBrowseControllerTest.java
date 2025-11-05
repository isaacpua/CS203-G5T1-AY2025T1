package com.tariff.tariff_backend.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyRequest;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyResponse;
import com.tariff.tariff_backend.dto.CalculationDTO.TransactionLineDTO;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.repository.TariffRepo;
import com.tariff.tariff_backend.service.CalculationService;
import com.tariff.tariff_backend.service.CalculatorHistoryService;
import com.tariff.tariff_backend.service.JwtService;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(properties = {
    // **FIXED**: Added MODE=PostgreSQL and NON_KEYWORDS=USER,YEAR
    "spring.datasource.url=jdbc:h2:mem:testdb;INIT=CREATE SCHEMA IF NOT EXISTS TARIFFS;MODE=PostgreSQL;NON_KEYWORDS=USER,YEAR",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "spring.datasource.username=sa",
    "spring.datasource.password=password",
    "spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.H2Dialect",
    "spring.jpa.hibernate.ddl-auto=create-drop",
    "jwt.secret=a-very-long-and-random-secret-key-for-testing-purposes-only-123456789"
})
class TariffBrowseControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private TariffRepo tariffRepo;

    @MockBean
    private CalculationService calculationService;

    @MockBean
    private CalculatorHistoryService calculatorHistoryService;

    @MockBean
    private JwtService jwtService;

    @Test
    @WithMockUser
    void search_ShouldReturnPaginatedResults() throws Exception {
        // --- Arrange ---
        Tariff dummyTariff = new Tariff();
        dummyTariff.setTariffId("test-id-123"); 
        dummyTariff.setDescriptionwcountry("Test Product");
        
        Page<Tariff> dummyPage = new PageImpl<>(List.of(dummyTariff), PageRequest.of(0, 10), 1);

        when(tariffRepo.searchNative(
            eq(156), eq(840), eq("wheat"), eq(null), eq(null), any(PageRequest.class)
        )).thenReturn(dummyPage);

        // --- Act & Assert ---
        mockMvc.perform(get("/api/v1/tariffs/search")
                .param("fromId", "156")
                .param("toId", "840")
                .param("q", "wheat")
                .param("page", "0")
                .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1))
                // **FIXED**: The field is 'tariffId' (camelCase)
                .andExpect(jsonPath("$.content[0].tariffId").value("test-id-123"))
                .andExpect(jsonPath("$.content[0].descriptionwcountry").value("Test Product"));
    }

    @Test
    @WithMockUser
    void calculate_ShouldReturnCalculationResponse() throws Exception {
        // --- Arrange ---
        CalculateDutyRequest request = new CalculateDutyRequest("tariff-123", new BigDecimal("1000"), new BigDecimal("10"), true);
        CalculateDutyResponse response = new CalculateDutyResponse(1, "tariff-123", new BigDecimal("150.0"));

        when(calculationService.calculateAndStore(any(CalculateDutyRequest.class))).thenReturn(response);

        // --- Act & Assert ---
        mockMvc.perform(post("/api/v1/tariffs/calc")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                // **FIXED**: The field is 'total' (from your DTO)
                .andExpect(jsonPath("$.total").value(150.0)); 
    }

    @Test
    @WithMockUser(username = "test-user")
    void getHistory_ShouldReturnTransactionList() throws Exception {
        // --- Arrange ---
        TransactionLineDTO historyItem = new TransactionLineDTO(1, Instant.now(), Collections.emptyMap());

        when(calculatorHistoryService.viewHistory()).thenReturn(List.of(historyItem));

        // --- Act & Assert ---
        mockMvc.perform(get("/api/v1/tariffs/transactionHistory"))
                .andExpect(status().isOk())
                // **FIXED**: The field is 'transactionId' (camelCase)
                .andExpect(jsonPath("$[0].transactionId").value(1)); 
    }
}