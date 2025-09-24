package com.tariff.tariff_backend.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UsernameUpdateDTO {
    @NotBlank(message = "Username cannot be blank")
    @Size(min = 1, max = 50, message = "Username must be between 1 and 50 characters")
    private String username;
}
